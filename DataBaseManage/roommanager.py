from psycopg2.extras import RealDictCursor
from utils.schema import Room, SimpleRack
from DataBaseManage.connection import BaseManager


class RoomManager(BaseManager):
    def createRoom(self, name: str, height: int, datacenter_name: str) -> Room:
        """
        Create a new room in a datacenter.

        Args:
            name (str): Name of the room
            height (int): Height capacity for the room
            datacenter_name (str): name of the datacenter this room belongs to

        Returns:
            Room: Room object if created successfully, None otherwise
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Check if datacenter exists
                cursor.execute(
                    "SELECT name FROM datacenters WHERE name = %s",
                    (datacenter_name,),
                )
                dc_data = cursor.fetchone()
                if dc_data is None:
                    raise Exception(
                        f"Datacenter named {datacenter_name} does not exist"
                    )

                new_room = Room(
                    name=name,
                    height=height,
                    n_racks=0,
                    racks=[],
                    n_hosts=0,
                    dc_name=dc_data["name"],
                )

                # Insert the new room
                cursor.execute(
                    "INSERT INTO rooms (name, height, dc_name) VALUES (%s, %s, %s)",
                    (new_room.name, new_room.height, new_room.dc_name),
                )
                conn.commit()

                return new_room

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
                    raise Exception(f"Room with name {room_name} not found")


                # Get full rack information for this room
                cursor.execute("SELECT * FROM racks WHERE room_name = %s", (room_name,))
                racks_data = cursor.fetchall()

                # calculate the count of hosts and capacity of racks
                racks = []
                for rack_data in racks_data:
                    # Get hosts for this rack
                    cursor.execute(
                        "SELECT * FROM hosts WHERE rack_name = %s",
                        (rack_data["name"],),
                    )
                    hosts_data = cursor.fetchall()
                    # Calculate the number of hosts in this rack
                    n_hosts = len(hosts_data)
                    already_used_capacity = sum(host["height"] for host in hosts_data)
                    capacity = rack_data["height"] - already_used_capacity
                    racks.append(
                        SimpleRack(
                            name=rack_data["name"],
                            height=rack_data["height"],
                            capacity=capacity,
                            n_hosts=n_hosts,
                            service_name=rack_data["service_name"],
                            room_name=room_data["name"],
                        )
                    )
                # Calculate the number of hosts in the room
                cursor.execute(
                    "SELECT COUNT(*) FROM hosts WHERE room_name = %s", (room_name,)
                )
                n_hosts = cursor.fetchone()[0]
                # Create and return the Room object
                return Room(
                    name=room_data["name"],
                    height=room_data["height"],
                    n_racks=room_data["n_racks"],
                    racks=racks,
                    n_hosts=n_hosts,
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
        old_name: str,
        new_name: str | None = None,
        height: int | None = None,
        dc_name: str | None = None,
    ) -> bool:
        """
        Update a room's information.

        Args:
            old_name (str): Name of the room to update
            new_name (str, optional): New name for the room
            height (int, optional): New height for the room
            dc_name (str, optional): New datacenter name for the room

        Returns:
            bool: True if room was successfully updated, False if not found
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # First check if room exists
                cursor.execute("SELECT name FROM rooms WHERE name = %s", (old_name,))
                if cursor.fetchone() is None:
                    return False

                # Build the update query based on provided parameters
                update_params = []
                query_parts = []

                if height is not None:
                    query_parts.append("height = %s")
                    update_params.append(height)

                if new_name is not None:
                    query_parts.append("name = %s")
                    update_params.append(new_name)
                if dc_name is not None:
                    # Check if new datacenter exists
                    cursor.execute(
                        "SELECT name FROM datacenters WHERE name = %s", (dc_name,)
                    )
                    if cursor.fetchone() is None:
                        raise Exception(
                            f"Datacenter with name {dc_name} does not exist"
                        )
                    query_parts.append("dc_name = %s")
                    update_params.append(dc_name)

                if not query_parts:
                    # Nothing to update
                    return True

                query = f"UPDATE rooms SET {', '.join(query_parts)} WHERE name = %s"
                update_params.append(old_name)
                # Execute the update query
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
    def deleteRoom(self, room_name: str) -> bool:
        """
        Delete a room from the database.

        Args:
            room_name (str): name of the room to delete

        Returns:
            bool: True if room was successfully deleted, False if not found
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # First check if room exists and get its datacenter_id
                cursor.execute(
                    "SELECT dc_name FROM rooms WHERE name = %s", (room_name,)
                )
                room_data = cursor.fetchone()

                if room_data is None:
                    return False

                # Delete the room
                cursor.execute("DELETE FROM rooms WHERE name = %s", (room_name,))
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
