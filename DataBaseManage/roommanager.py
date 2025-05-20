from psycopg2.extras import RealDictCursor
from utils.schema import Room, SimpleRack
from DataBaseManage.connection import BaseManager


class RoomManager(BaseManager):
    def createRoom(self, name: str, height: int, datacenter_name: str) -> str:
        """
        Create a new room in a datacenter.

        Args:
            name (str): Name of the room
            height (int): Height capacity for the room
            datacenter_name (str): name of the datacenter this room belongs to

        Returns:
            str: Name of the newly created room
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Check if datacenter exists
                cursor.execute(
                    "SELECT name FROM datacenters WHERE datacenter_name = %s", (datacenter_name,)
                )
                dc_data = cursor.fetchone()
                if dc_data is None:
                    raise Exception(
                        f"Datacenter named {datacenter_name} does not exist"
                    )

                # Generate a new UUID for the room
                # Insert the new room
                cursor.execute(
                    "INSERT INTO rooms (name, height, dc_name) VALUES (%s, %s, %s)",
                    (name, height, dc_data["name"]),
                )
                conn.commit()
                return name

        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    # READ operations
    def getRoom(self, room_name: str) -> Room | None:
        """
        Get a room by name.

        Args:
            room_name (str): Name of the room to retrieve

        Returns:
            Room: Room object if found, None otherwise
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT * FROM rooms WHERE name = %s",
                    (room_name,),
                )
                room_data = cursor.fetchone()

                if room_data is None:
                    return None

                # Get full rack information for this room
                cursor.execute("SELECT * FROM racks WHERE room_name = %s", (room_name,))
                racks_data = cursor.fetchall()

                # calculate the count of hosts and capacity of racks
                for rack_data in racks_data:
                    hosts = rack_data.hosts
                    already_used_capacity = 
                    n_hosts = 0
                    hosts_data = cursor.fetchall()
                    

                # Create SimpleRack objects

                # Create and return the Room object
                return Room(
                    id=room_data["id"],
                    name=room_data["name"],
                    height=room_data["height"],
                    n_racks=room_data["n_racks"],
                    racks=racks,
                    n_hosts=len(hosts_data)
                    dc_id=room_data["dc_id"],
                    dc_name=room_data["dc_name"],
                )

        except Exception as e:
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    # UPDATE operations
    def updateRoom(
        self,
        room_id: str,
        name: str | None = None,
        height: int | None = None,
        dc_id: str | None = None,
    ) -> bool:
        """
        Update a room's information.

        Args:
            room_id (str): ID of the room to update
            name (str, optional): New name for the room
            height (int, optional): New height for the room
            dc_id (str, optional): New datacenter ID for the room

        Returns:
            bool: True if room was successfully updated, False if not found
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # First check if room exists
                cursor.execute("SELECT id FROM rooms WHERE id = %s", (room_id,))
                if cursor.fetchone() is None:
                    return False

                # Build the update query based on provided parameters
                update_params = []
                query_parts = []

                if name is not None:
                    query_parts.append("name = %s")
                    update_params.append(name)

                if height is not None:
                    query_parts.append("height = %s")
                    update_params.append(height)

                if dc_id is not None:
                    # TODO: implement logic of moving room to a new dc
                    # check if new datacenter exists
                    cursor.execute(
                        "SELECT id FROM datacenters WHERE id = %s", (dc_id,)
                    )
                    if cursor.fetchone() is None:
                        raise Exception(
                            f"Datacenter with ID {dc_id} does not exist"
                        )
                    # delete the room from the old datacenter
                    # find datacenter id
                    cursor.execute(
                        "SELECT dc_id FROM rooms WHERE id = %s", (room_id,)
                    )
                    old_dc_id = cursor.fetchone()["dc_id"]
                    cursor.execute(
                        "UPDATE datacenters SET n_rooms = n_rooms - 1 WHERE id = %s",
                        (old_dc_id,),
                    )
                    # add the room to the new datacenter
                    cursor.execute(
                        "UPDATE datacenters SET n_rooms = n_rooms + 1 WHERE id = %s",
                        (dc_id,),
                    )
                    query_parts.append("dc_id = %s")
                    update_params.append(dc_id)
                    query_parts.append("dc_name = %s")
                    # get the name of the new datacenter
                    cursor.execute(
                        "SELECT name FROM datacenters WHERE id = %s", (dc_id,)
                    )
                    dc_name = cursor.fetchone()["name"]
                    update_params.append(dc_name)

                if not query_parts:
                    # Nothing to update
                    return True

                query = f"UPDATE rooms SET {', '.join(query_parts)} WHERE id = %s"
                update_params.append(room_id)

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
    def deleteRoom(self, room_id: str) -> bool:
        """
        Delete a room from the database.

        Args:
            room_id (str): ID of the room to delete

        Returns:
            bool: True if room was successfully deleted, False if not found
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # First check if room exists and get its datacenter_id
                cursor.execute("SELECT dc_id FROM rooms WHERE id = %s", (room_id,))
                room_data = cursor.fetchone()

                if room_data is None:
                    return False

                datacenter_id = room_data["dc_id"]

                # Check if room has any racks (optional: prevent deletion if it has dependencies)
                cursor.execute(
                    "SELECT COUNT(*) FROM racks WHERE room_id = %s", (room_id,)
                )
                rack_count = cursor.fetchone()["count"]

                if rack_count > 0:
                    # You may want to raise a custom exception here instead to indicate that the room has dependencies
                    raise Exception(
                        f"Cannot delete room with ID {room_id} because it contains {rack_count} racks"
                    )

                # Delete the room
                cursor.execute("DELETE FROM rooms WHERE id = %s", (room_id,))

                # Update the room count in the datacenter
                cursor.execute(
                    "UPDATE datacenters SET n_rooms = n_rooms - 1 WHERE id = %s",
                    (datacenter_id,),
                )

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
