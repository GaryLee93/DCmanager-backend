import os
from psycopg2.extras import RealDictCursor
from utils.schema import Rack, SimpleHost
from DataBaseManage.connection import BaseManager


class RackManager(BaseManager):

    # CREATE operations
    def createRack(self, name: str, height: int, room_id: str) -> str:
        """
        Create a new rack in a room.

        Args:
            name (str): Name of the rack
            height (int): Height capacity for the rack
            room_id (str): ID of the room this rack belongs to

        Returns:
            str: ID of the newly created rack
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:

                cursor.execute(
                    "SELECT id, name, dc_id, dc_name FROM rooms WHERE id = %s",
                    (room_id,),
                )
                room_data = cursor.fetchone()

                if room_data is None:
                    raise Exception(f"Room with ID {room_id} does not exist")

                # Generate a new UUID for the rack
                cursor.execute("SELECT gen_random_uuid()")
                rack_id = cursor.fetchone()["gen_random_uuid"]

                # Insert the new rack
                cursor.execute(
                    "INSERT INTO racks (id, name, height, n_hosts, service_id, service_name, dc_id, dc_name, room_id, room_name) VALUES (%s, %s, %s, 0, %s, %s, %s)",
                    (
                        rack_id,
                        name,
                        height,
                        None,
                        None,
                        room_data["dc_id"],
                        room_data["dc_name"],
                        room_data["id"],
                        room_data["name"],
                    ),
                )

                conn.commit()
                return rack_id

        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    # READ operations
    def getRack(self, rack_id: str) -> Rack | None:
        """
        Get a rack by ID.

        Args:
            rack_id (str): ID of the rack to retrieve

        Returns:
            Rack: Rack object if found, None otherwise
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT * FROM racks WHERE id = %s",
                    (rack_id,),
                )
                result = cursor.fetchone()

                if result is None:
                    return None

                # Get hosts for this rack
                cursor.execute(
                    "SELECT * FROM hosts WHERE rack_id = %s",
                    (rack_id,),
                )
                hosts_data = cursor.fetchall()

                # Convert to SimpleHost objects
                hosts = [
                    SimpleHost(
                        id=host_data["id"],
                        name=host_data["name"],
                        height=host_data["height"],
                        ip=host_data["ip"],
                        running=host_data["running"],
                        rack_id=host_data["rack_id"],
                        pos=host_data["pos"],
                    )
                    for host_data in hosts_data
                ]

                # Create and return the Rack object
                return Rack(
                    id=result["id"],
                    name=result["name"],
                    height=result["height"],
                    capacity=result["capacity"],
                    n_hosts=result["n_hosts"],
                    hosts=hosts,
                    service_id=result["service_id"],
                    service_name=result["service_name"],
                    dc_id=result["dc_id"],
                    dc_name=result["dc_name"],
                    room_id=result["room_id"],
                    room_name=result["room_name"],
                )

        except Exception as e:
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    # UPDATE operations
    def updateRack(
        self,
        rack_id: str,
        name: str | None = None,
        height: int | None = None,
        service_id: str | None = None,
        room_id: str | None = None,
    ) -> bool:
        """
        Update a rack's information.

        Args:
            rack_id (str): ID of the rack to update
            name (str, optional): New name for the rack
            height (int, optional): New height for the rack
            service_id (str, optional): New service ID for the rack
            room_id (str, optional): ID of the room this rack belongs to

        Returns:
            bool: True if rack was successfully updated, False if not found
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # First check if rack exists and get its current service_id
                cursor.execute("SELECT service_id FROM racks WHERE id = %s", (rack_id,))
                rack_info = cursor.fetchone()

                if rack_info is None:
                    return False

                current_service_id = rack_info["service_id"]

                # Check if service exists (if a new one is provided)
                if service_id is not None and service_id != current_service_id:
                    cursor.execute(
                        "SELECT id FROM services WHERE id = %s", (service_id,)
                    )
                    if cursor.fetchone() is None:
                        raise Exception(f"Service with ID {service_id} does not exist")

                # Build the update query based on provided parameters
                update_params = []
                query_parts = []

                if name is not None:
                    query_parts.append("name = %s")
                    update_params.append(name)

                if height is not None:
                    query_parts.append("height = %s")
                    update_params.append(height)

                if service_id is not None:
                    query_parts.append("service_id = %s")
                    update_params.append(service_id)

                if room_id is not None:
                    # TODO: implement logic of moving rack to a new room
                    # check if new room exists
                    cursor.execute(
                        "SELECT id FROM rooms WHERE id = %s", (room_id,)
                    )
                    if cursor.fetchone() is None:
                        raise Exception(f"Room with ID {room_id} does not exist")
                    query_parts.append("room_id = %s")
                    update_params.append(room_id)

                if not query_parts:
                    # Nothing to update
                    return True

                query = f"UPDATE racks SET {', '.join(query_parts)} WHERE id = %s"
                update_params.append(rack_id)

                cursor.execute(query, tuple(update_params))

                conn.commit()

                # Check if any rows were affected
                return cursor.rowcount > 0

        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    # DELETE operations
    def deleteRack(self, rack_id: str) -> bool:
        """
        Delete a rack from the database.

        Args:
            rack_id (str): ID of the rack to delete

        Returns:
            bool: True if rack was successfully deleted, False if not found
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # First check if rack exists and get its room_id, datacenter_id, and service_id
                cursor.execute(
                    "SELECT id, room_id, dc_id, service_id FROM racks WHERE id = %s",
                    (rack_id,),
                )
                rack_info = cursor.fetchone()

                if rack_info is None:
                    return False

                room_id = rack_info["room_id"]
                datacenter_id = rack_info["dc_id"]
                service_id = rack_info["service_id"]

                # Check if rack has any hosts (optional: prevent deletion if it has dependencies)
                cursor.execute(
                    "SELECT COUNT(*) FROM hosts WHERE rack_id = %s", (rack_id,)
                )
                host_count = cursor.fetchone()["count"]

                if host_count > 0:
                    # You may want to raise a custom exception here instead
                    # to indicate that the rack has dependencies
                    raise Exception(
                        f"Cannot delete rack with ID {rack_id} because it contains {host_count} hosts"
                    )

                # Delete the rack
                cursor.execute("DELETE FROM racks WHERE id = %s", (rack_id,))
                conn.commit()

                # Check if any rows were affected
                return cursor.rowcount > 0

        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)
