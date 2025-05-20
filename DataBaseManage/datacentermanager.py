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
        ip_ranges: list[IP_Range] | None = None,
    ) -> DataCenter | None:
        """
        Create a new datacenter in the database.

        Args:
            name (str): Name of the datacenter
            default_height (int, optional): Default rack height for the datacenter. Defaults to 42.
            ip_ranges (list[IP_Range], optional): IP ranges for the datacenter. Defaults to None.

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
                    INSERT INTO datacenters (name, height, n_rooms, n_racks, n_hosts)
                    VALUES (%s, %s, 0, 0, 0)
                    RETURNING id, name, height, n_rooms, n_racks, n_hosts
                    """,
                    (name, default_height),
                )

                # Commit the transaction
                conn.commit()

                # Get the newly created datacenter data
                new_datacenter = cursor.fetchone()

                if not new_datacenter:
                    return None

                # Add IP ranges if provided
                ip_range_objects = []
                if ip_ranges and len(ip_ranges) > 0:
                    ip_range_manager = IPRangeManager()
                    for ip_range in ip_ranges:
                        added_range = ip_range_manager.add_ip_range(
                            new_datacenter["id"], ip_range.start_IP, ip_range.end_IP
                        )
                        ip_range_objects.append(added_range)

                # Create and return a DataCenter object
                return DataCenter(
                    id=new_datacenter["id"],
                    name=new_datacenter["name"],
                    height=new_datacenter["height"],
                    n_rooms=new_datacenter["n_rooms"],
                    rooms=[],  # New datacenter has no rooms yet
                    n_racks=new_datacenter["n_racks"],
                    n_hosts=new_datacenter["n_hosts"],
                    ip_ranges=ip_range_objects,
                )

        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    def getDatacenter(self, datacenter_id: str) -> DataCenter | None:
        """
        Get datacenters information.
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get the specific datacenter
                cursor.execute(
                    "SELECT * FROM datacenters WHERE id = %s", (datacenter_id,)
                )
                data = cursor.fetchone()
                if not data:
                    return None

                # Get rooms for this datacenter
                cursor.execute("SELECT * FROM rooms WHERE dc_id = %s", (datacenter_id,))
                rooms_data = cursor.fetchall()

                # Convert to SimpleRoom objects
                rooms = [
                    SimpleRoom(
                        id=room_data["id"],
                        name=room_data["name"],
                        height=room_data["height"],
                        n_racks=room_data["n_racks"],
                        n_hosts=room_data["n_hosts"],
                        dc_id=room_data["dc_id"],
                    )
                    for room_data in rooms_data
                ]

                # Get IP ranges for this datacenter
                ip_range_manager = IPRangeManager()
                ip_ranges = ip_range_manager.get_ip_ranges(datacenter_id)

                # Create and return a DataCenter object
                return DataCenter(
                    id=data["id"],
                    name=data["name"],
                    height=data["height"],
                    rooms=rooms,
                    n_rooms=data["n_rooms"],
                    n_racks=data["n_racks"],
                    n_hosts=data["n_hosts"],
                    ip_ranges=ip_ranges,
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
                    datacenter_id = data["id"]
                    # Get rooms for this datacenter
                    cursor.execute(
                        "SELECT * FROM rooms WHERE dc_id = %s", (datacenter_id,)
                    )

                    # Create DataCenter object and append to list
                    datacenters.append(
                        SimpleDataCenter(
                            id=data["id"],
                            name=data["name"],
                            height=data["height"],
                            n_rooms=data["n_rooms"],
                            n_racks=data["n_racks"],
                            n_hosts=data["n_hosts"],
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
        datacenter_id: str,
        name: str | None = None,
        default_height: int | None = None,
        ip_ranges: list[IP_Range] | None = None,
    ) -> bool:
        """
        Update an existing datacenter in the database.

        Args:
            datacenter_id (str): ID of the datacenter to update
            name (str, optional): New name for the datacenter
            default_height (int, optional): New default rack height for the datacenter
            ip_ranges (list[IP_Range], optional): New IP ranges for the datacenter

        Returns:
            bool: True if datacenter was successfully updated, False if not found
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # First check if datacenter exists
                cursor.execute(
                    "SELECT * FROM datacenters WHERE id = %s", (datacenter_id,)
                )
                if cursor.fetchone() is None:
                    return False

                # Prepare update query parts
                query_parts = []
                update_params = []

                if name is not None:
                    query_parts.append("name = %s")
                    update_params.append(name)

                if default_height is not None:
                    query_parts.append("height = %s")
                    update_params.append(default_height)

                # If no database updates requested but ip_ranges provided,
                # we'll still need to process IP ranges
                if query_parts:
                    # Add updated_at to be updated
                    query_parts.append("updated_at = CURRENT_TIMESTAMP")

                    # Build and execute update query
                    query = f"UPDATE datacenters SET {', '.join(query_parts)} WHERE id = %s RETURNING *"
                    update_params.append(datacenter_id)

                    cursor.execute(query, update_params)
                    conn.commit()

                # Handle IP ranges if provided
                ip_range_manager = IPRangeManager()
                if ip_ranges is not None:
                    # Delete existing IP ranges for this datacenter
                    cursor.execute(
                        "DELETE FROM ip_ranges WHERE id = %s", (datacenter_id,)
                    )
                    conn.commit()

                    # Add new IP ranges
                    for ip_range in ip_ranges:
                        ip_range_manager.add_ip_range(
                            datacenter_id, ip_range.start_IP, ip_range.end_IP
                        )

                return True

        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    def deleteDatacenter(self, datacenter_id):
        """
        Delete a datacenter from the database.

        Args:
            datacenter_id (str): ID of the datacenter to delete

        Returns:
            bool: True if datacenter was successfully deleted, False if not found
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # First check if datacenter exists
                cursor.execute(
                    "SELECT id FROM datacenters WHERE id = %s", (datacenter_id,)
                )
                if cursor.fetchone() is None:
                    return False

                # Check if datacenter has any rooms
                cursor.execute(
                    "SELECT COUNT(*) FROM rooms WHERE dc_id = %s", (datacenter_id,)
                )
                room_count = cursor.fetchone()["count"]

                if room_count > 0:
                    raise Exception(
                        f"Cannot delete datacenter with ID {datacenter_id} because it contains {room_count} rooms"
                    )

                # Delete associated IP ranges first
                cursor.execute(
                    "DELETE FROM ip_ranges WHERE dc_id = %s", (datacenter_id,)
                )

                # Delete the datacenter
                cursor.execute(
                    "DELETE FROM datacenters WHERE id = %s", (datacenter_id,)
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
