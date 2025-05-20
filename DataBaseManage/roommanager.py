from psycopg2.extras import RealDictCursor
from utils.schema import Room, SimpleRack
from DataBaseManage.connection import BaseManager


class RoomManager(BaseManager):
    # CREATE operations
    def createRoom(self, name: str, height: int, datacenter_id: str) -> str:
        """
        Create a new room in a datacenter.

        Args:
            name (str): Name of the room
            height (int): Height capacity for the room
            datacenter_id (str): ID of the datacenter this room belongs to

        Returns:
            str: ID of the newly created room
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Check if datacenter exists
                cursor.execute(
                    "SELECT id, name FROM datacenters WHERE id = %s", (datacenter_id,)
                )
                dc_data = cursor.fetchone()
                if dc_data is None:
                    raise Exception(
                        f"Datacenter with ID {datacenter_id} does not exist"
                    )

                # Generate a new UUID for the room
                cursor.execute("SELECT gen_random_uuid()")
                room_id = cursor.fetchone()["gen_random_uuid"]

                # Insert the new room
                cursor.execute(
                    "INSERT INTO rooms (id, name, height, n_racks, n_hosts, dc_id, dc_name) VALUES (%s, %s, %s, 0, 0, %s, %s)",
                    (room_id, name, height, dc_data["id"], dc_data["name"]),
                )

                # Update the room count in the datacenter
                cursor.execute(
                    "UPDATE datacenters SET n_rooms = n_rooms + 1 WHERE id = %s",
                    (datacenter_id,),
                )

                conn.commit()
                return room_id

        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    # READ operations
    def getRoom(self, room_id: str) -> Room | None:
        """
        Get a room by ID.

        Args:
            room_id (str): ID of the room to retrieve

        Returns:
            Room: Room object if found, None otherwise
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT * FROM rooms WHERE id = %s",
                    (room_id,),
                )
                room_data = cursor.fetchone()

                if room_data is None:
                    return None

                # Get full rack information for this room
                cursor.execute("SELECT * FROM racks WHERE room_id = %s", (room_id,))
                racks_data = cursor.fetchall()

                # Create SimpleRack objects
                racks = [
                    SimpleRack(
                        id=rack_data["id"],
                        name=rack_data["name"],
                        height=rack_data["height"],
                        capacity=rack_data["capacity"],
                        n_hosts=rack_data["n_hosts"],
                        service_id=rack_data["service_id"],
                        service_name=rack_data["service_name"],
                        room_id=room_id,
                    )
                    for rack_data in racks_data
                ]

                # Create and return the Room object
                return Room(
                    id=room_data["id"],
                    name=room_data["name"],
                    height=room_data["height"],
                    n_racks=room_data["n_racks"],
                    racks=racks,
                    n_hosts=room_data["n_hosts"],
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
                    pass

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
