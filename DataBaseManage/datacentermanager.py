from psycopg2.extras import RealDictCursor
from utils.schema import DataCenter, SimpleDataCenter, SimpleRoom, IP_Range
from DataBaseManage import IPRangeManager
from DataBaseManage.connection import BaseManager


class DatacenterManager(BaseManager):
    """Class for managing datacenter operations"""

    # Datacenter operations
    def createDatacenter(
        self,
        name: str,
        default_height: int = 42,
    ) -> DataCenter | None:
        """
        Create a new datacenter in the database.

        Args:
            name (str): Name of the datacenter
            default_height (int, optional): Default rack height for the datacenter. Defaults to 42.

        Returns:
            DataCenter: A DataCenter object representing the newly created datacenter.
            None: If creation fails
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Insert the new datacenter
                cursor.execute(
                    """
                    INSERT INTO datacenters (name, height)
                    VALUES (%s, %s)
                    RETURNING name, height
                    """,
                    (name, default_height),
                )

                # Commit the transaction
                conn.commit()

                # Get the newly created datacenter data
                new_datacenter = cursor.fetchone()

                if not new_datacenter:
                    return None

                # Create and return a DataCenter object
                return DataCenter(
                    name=new_datacenter["name"],
                    height=new_datacenter["height"],
                    n_rooms=0,  # New datacenter has no rooms yet
                    n_racks=0,  # New datacenter has no racks yet
                    n_hosts=0,  # New datacenter has no hosts yet
                )

        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    def getDatacenter(self, datacenter_name: str) -> DataCenter | None:
        """
        Get datacenters information.
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get the specific datacenter
                cursor.execute(
                    "SELECT * FROM datacenters WHERE name = %s", (datacenter_name,)
                )
                data = cursor.fetchone()
                if not data:
                    return None

                # Get rooms for this datacenter
                cursor.execute("SELECT * FROM rooms WHERE dc_name = %s", (datacenter_name,))
                rooms_data = cursor.fetchall()

                # Convert to SimpleRoom objects
                rooms = [ ]
                all_racks_num = 0
                all_hosts_num = 0
                for room_data in rooms_data:
                    room_name = room_data["name"]
                    room_height = room_data["height"]
                    # count racks in this room
                    cursor.execute(
                        "SELECT COUNT(*) FROM racks WHERE room_name = %s", (room_name,)
                    )
                    n_racks = cursor.fetchone()["count"]
                    # count hosts in this room
                    cursor.execute(
                        "SELECT COUNT(*) FROM hosts WHERE room_name = %s", (room_name,)
                    )
                    n_hosts = cursor.fetchone()["count"]
                    # Create SimpleRoom object
                    rooms.append(
                        SimpleRoom(
                            name=room_name,
                            height=room_height,
                            n_racks=n_racks,
                            n_hosts=n_hosts,
                            dc_name=datacenter_name,
                        )
                    )
                    all_racks_num += n_racks
                    all_hosts_num += n_hosts

                # Create and return a DataCenter object
                return DataCenter(
                    name=data["name"],
                    height=data["height"],
                    rooms=rooms,
                    n_rooms=len(rooms),
                    n_racks=all_racks_num,
                    n_hosts=all_hosts_num,
                )
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    def getAllDatacenters(self) -> list[SimpleDataCenter]:
        """
        Get all datacenters.

        Returns:
            list: List of DataCenter objects
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM datacenters ORDER BY name")
                datacenters_data = cursor.fetchall()

                # Create a list to store DataCenter objects
                datacenters = []

                # Process each datacenter
                for data in datacenters_data:
                    datacenter_name = data["name"]
                    # Get rooms for this datacenter
                    cursor.execute(
                        "SELECT * FROM rooms WHERE dc_name = %s", (datacenter_name,)
                    )
                    # Count the number of rooms
                    cursor.execute(
                        "SELECT COUNT(*) FROM rooms WHERE dc_name = %s", (datacenter_name,)
                    )
                    n_rooms = cursor.fetchone()["count"]
                    # Count the number of racks
                    cursor.execute(
                        "SELECT COUNT(*) FROM racks WHERE dc_name = %s", (datacenter_name,)
                    )
                    n_racks = cursor.fetchone()["count"]
                    # Count the number of hosts
                    cursor.execute(
                        "SELECT COUNT(*) FROM hosts WHERE dc_name = %s", (datacenter_name,)
                    )
                    n_hosts = cursor.fetchone()["count"]
                    # Create DataCenter object and append to list
                    datacenters.append(
                        SimpleDataCenter(
                            name=data["name"],
                            height=data["height"],
                            n_rooms=n_rooms,
                            n_racks=n_racks,
                            n_hosts=n_hosts,
                        )
                    )

                return datacenters

        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    def updateDatacenter(
        self,
        old_name: str,
        new_name: str | None = None,
        default_height: int | None = None,
    ) -> bool:
        """
        Update an existing datacenter in the database.

        Args:
            old_name (str): name of the datacenter to update
            new_name (str, optional): New name for the datacenter
            default_height (int, optional): New default rack height for the datacenter

        Returns:
            bool: True if datacenter was successfully updated, False if not found
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # First check if datacenter exists
                cursor.execute(
                    "SELECT * FROM datacenters WHERE name = %s", (old_name,)
                )
                if cursor.fetchone() is None:
                    return False

                # Prepare update query parts
                query_parts = []
                update_params = []

                if new_name is not None:
                    query_parts.append("name = %s")
                    update_params.append(new_name)

                if default_height is not None:
                    query_parts.append("height = %s")
                    update_params.append(default_height)

                # If no database updates requested but ip_ranges provided,
                # we'll still need to process IP ranges
                if query_parts:
                    # Add updated_at to be updated
                    query_parts.append("updated_at = CURRENT_TIMESTAMP")

                    # Build and execute update query
                    query = f"UPDATE datacenters SET {', '.join(query_parts)} WHERE name = %s RETURNING *"
                    update_params.append(new_name)

                    cursor.execute(query, update_params)
                    conn.commit()

                return True

        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    def deleteDatacenter(self, datacenter_name: str) -> bool:
        """
        Delete a datacenter from the database.

        Args:
            datacenter_name (str): name of the datacenter to delete

        Returns:
            bool: True if datacenter was successfully deleted, False if not found
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # First check if datacenter exists
                cursor.execute(
                    "SELECT name FROM datacenters WHERE name = %s", (datacenter_name,)
                )
                if cursor.fetchone() is None:
                    return False

                # Check if datacenter has any rooms
                cursor.execute(
                    "SELECT COUNT(*) FROM rooms WHERE name = %s", (datacenter_name,)
                )
                room_count = cursor.fetchone()["count"]

                if room_count > 0:
                    raise Exception(
                        f"Cannot delete datacenter with ID {datacenter_name} because it contains {room_count} rooms"
                    )

                # Delete the datacenter
                cursor.execute(
                    "DELETE FROM datacenters WHERE name = %s", (datacenter_name,)
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
