import os
from psycopg2.extras import RealDictCursor
from utils.schema import Rack, Host
from DataBaseManage.connection import BaseManager


class RackManager(BaseManager):

    # CREATE operations
    def createRack(self, name: str, height: int, room_name: str) -> Rack:
        """
        Create a new rack in a room.

        Args:
            name (str): Name of the rack
            height (int): Height capacity for the rack
            room_name (str): ID of the room this rack belongs to

        Returns:
            str: name of the newly created rack
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:

                cursor.execute(
                    "SELECT name, dc_name FROM rooms WHERE name = %s",
                    (room_name,),
                )
                room_data = cursor.fetchone()

                if room_data is None:
                    return None

                new_rack = Rack(
                    name=name,
                    height=height,
                    capacity=height,
                    n_hosts=0,
                    hosts=[],
                    service_name=None,  # Service name is not provided in the current context
                    dc_name=room_data["dc_name"],
                    room_name=room_data["name"],
                )

                # Insert the new rack
                cursor.execute(
                    "INSERT INTO racks (name, height, service_name, dc_name, room_name) VALUES (%s, %s, %s, %s, %s)",
                    (
                        new_rack.name,
                        new_rack.height,
                        new_rack.service_name,
                        new_rack.dc_name,
                        new_rack.room_name,
                    ),
                )

                conn.commit()
                return new_rack

        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    # READ operations
    def getRack(self, rack_name: str) -> Rack | None:
        """
        Get a rack by name.

        Args:
            rack_name(str): name of the rack to retrieve

        Returns:
            Rack: Rack object if found, None otherwise
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT * FROM racks WHERE name = %s",
                    (rack_name,),
                )
                result = cursor.fetchone()

                if result is None:
                    return None

                # Get hosts for this rack
                cursor.execute(
                    "SELECT * FROM hosts WHERE rack_name = %s",
                    (rack_name,),
                )
                hosts_data = cursor.fetchall()

                hosts = [
                    Host(
                        name=host_data["name"],
                        height=host_data["height"],
                        ip=host_data["ip"],
                        running=host_data["running"],
                        service_name=host_data["service_name"],
                        dc_name=host_data["dc_name"],
                        room_name=host_data["room_name"],
                        rack_name=host_data["rack_name"],
                        pos=host_data["pos"],
                    )
                    for host_data in hosts_data
                ]
                # Calculate the number of hosts
                n_hosts = len(hosts)
                # Calculate the capacity
                already_used = sum(host.height for host in hosts)
                # Calculate the remaining capacity
                capacity = result["height"] - already_used

                # Create and return the Rack object
                return Rack(
                    name=result["name"],
                    height=result["height"],
                    capacity=capacity,
                    n_hosts=len(hosts),
                    hosts=hosts,
                    service_name=result["service_name"],
                    dc_name=result["dc_name"],
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
        rack_name: str,
        name: str | None = None,
        height: int | None = None,
        room_name: str | None = None,
    ) -> bool:
        """
        Update a rack's information.

        Args:
            rack_name (str): name of the rack to update
            name (str, optional): New name for the rack
            height (int, optional): New height for the rack
            room_name (str, optional): name of the room this rack belongs to

        Returns:
            bool: True if rack was successfully updated, False if not found
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Build the update query based on provided parameters
                update_params = []
                query_parts = []

                if name is not None:
                    query_parts.append("name = %s")
                    update_params.append(name)

                if height is not None:
                    query_parts.append("height = %s")
                    update_params.append(height)

                if room_name is not None:
                    # TODO: implement logic of moving rack to a new room
                    # check if new room exists
                    cursor.execute(
                        "SELECT name, dc_name FROM rooms WHERE name = %s", (room_name,)
                    )
                    new_room_data = cursor.fetchone()

                    if new_room_data is None:
                       return False

                    new_dc_name = new_room_data["dc_name"]
                    print(new_room_data)

                    query_parts.append("room_name = %s")
                    update_params.append(room_name)

                    query_parts.append("dc_name = %s")
                    update_params.append(new_dc_name)

                if not query_parts:
                    # Nothing to update
                    return True

                query = f"UPDATE racks SET {', '.join(query_parts)} WHERE name = %s"
                update_params.append(rack_name)

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
    def deleteRack(self, rack_name: str) -> bool:
        """
        Delete a rack from the database.

        Args:
            rack_name (str): Name of the rack to delete

        Returns:
            bool: True if rack was successfully deleted, False if not found
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # First check if rack exists and get its room_id, datacenter_id, and service_id
                cursor.execute(
                    "SELECT name FROM racks WHERE name = %s",
                    (rack_name,),
                )
                rack_info = cursor.fetchone()

                if rack_info is None:
                    return False

                # Delete the rack
                cursor.execute("DELETE FROM racks WHERE name = %s", (rack_name,))
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
