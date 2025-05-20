from utils.schema import Host
from DataBaseManage.connection import BaseManager
from psycopg2.extras import RealDictCursor

# Todo
# if ip empty, allocate more ip
class HostManager(BaseManager):

    # CREATE operations
    def createHost(self, name: str, height: str, rack_name: str, pos: str) -> str:
        """
        Create a new host in a rack.

        Args:
            name (str): Name of the host
            height (int): Height of the host in rack units
            rack_name (str): Name of the rack this host belongs to
            pos (int): Position in the rack. If None, will use the next available position.

        Returns:
            str: ID of the newly created host
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Check if rack exists and get its room_id and datacenter_id
                cursor.execute(
                    "SELECT name, height, service_name, dc_name, room_name FROM racks WHERE name = %s",
                    (rack_name,),
                )
                rack_data = cursor.fetchone()

                if rack_data is None:
                    raise Exception(f"Rack with Name {rack_name} does not exist")

                # Get an available IP of service
                cursor.execute(
                    "SELECT ip FROM IPs WHERE service_name = %s AND assigned = FALSE ORDER BY ip DESC LIMIT 1",
                    (rack_data["service_name"],),
                )
                allocated_ip = cursor.fetchone()

                if allocated_ip is not None:
                    # Update the IP to be assigned and Decrease the available IP count
                    cursor.execute(
                        "UPDATE IPs SET assigned = TRUE WHERE ip = %s",
                        (allocated_ip,),
                    )

                # Insert host
                cursor.execute(
                    "INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (
                        name,
                        height,
                        allocated_ip,
                        True,
                        rack_data["service_name"],
                        rack_data["dc_name"],
                        rack_data["room_name"],
                        rack_data["name"],
                        pos,
                    ),
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
    def getHost(self, host_name: str) -> Host | None:
        """
        Get a host by name.

        Args:
            host_name (str): name of the host to retrieve

        Returns:
            Host: Host object if found, None otherwise
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT * FROM hosts WHERE name = %s",
                    (host_name,),
                )
                result = cursor.fetchone()

                if result is None:
                    return None

                # Create and return the Host object
                return result

        except Exception as e:
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    # UPDATE operations
    def updateHost(
        self,
        old_name: str,
        new_name: str | None = None,
        height: int | None = None,
        running: bool | None = None,
        rack_name=None,
    ):
        """
        Update a host's information.

        Args:
            old_name (str): Current name of the host
            new_name (str, optional): New name for the host
            height (int, optional): New height for the host
            running (bool, optional): New running status for the host
            rack_name (str, optional): New rack name for the host.
                User is not allowed to move the host to rack in different service or datacenter.

        Returns:
            bool: True if host was successfully updated, False if not found
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # First check if host exists and get its current information
                cursor.execute(
                    "SELECT name, rack_name, room_name, dc_name, service_name FROM hosts WHERE name = %s",
                    (old_name,),
                )
                host_data = cursor.fetchone()

                if host_data is None:
                    return False

                current_rack_name = host_data["rack_name"]
                current_room_name = host_data["room_name"]
                current_datacenter_name = host_data["dc_name"]
                current_service_name = host_data["service_name"]

                # Check if rack exists and get its room_id and datacenter_id if changing rack
                new_rack_data = None
                if rack_name is not None and rack_name != current_rack_name:
                    cursor.execute(
                        "SELECT name, room_name, room_name, dc_name, service_name FROM racks WHERE name = %s",
                        (rack_name,),
                    )
                    new_rack_data = cursor.fetchone()

                    if new_rack_data is None:
                        raise Exception(f"Rack with name {rack_name} does not exist")

                    if (
                        new_rack_data["service_name"] != current_service_name
                        or new_rack_data["dc_name"] != current_datacenter_name
                    ):
                        raise Exception(
                            f"Cannot move host to rack in different service or datacenter"
                        )

                # Build the update query based on provided parameters
                update_params = []
                query_parts = []

                if new_name is not None:
                    query_parts.append("name = %s")
                    update_params.append(new_name)

                if height is not None:
                    query_parts.append("height = %s")
                    update_params.append(height)

                if running is not None:
                    query_parts.append("running = %s")
                    update_params.append(running)

                if new_rack_data is not None:
                    query_parts.append("rack_name = %s")
                    update_params.append(new_rack_data["name"])

                    if new_rack_data["room_name"] != current_room_name:
                        query_parts.append("room_name = %s")
                        update_params.append(new_rack_data["room_name"])

                if not query_parts:
                    # Nothing to update
                    return True

                query = f"UPDATE hosts SET {', '.join(query_parts)} WHERE name = %s"
                update_params.append(old_name)

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
    def deleteHost(self, host_name: str) -> bool:
        """
        Delete a host from the database.

        Args:
            host_name (str): name of the host to delete

        Returns:
            bool: True if host was successfully deleted, False if not found
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # First check if host exists and get its rack_id, room_id, and datacenter_id
                cursor.execute(
                    "SELECT name, rack_name, room_name, dc_name FROM hosts WHERE name = %s",
                    (host_name,),
                )
                host_data = cursor.fetchone()

                if host_data is None:
                    return False

                rack_name = host_data["rack_name"]
                room_name = host_data["room_name"]
                datacenter_name = host_data["dc_name"]
                # Delete the host
                cursor.execute("DELETE FROM hosts WHERE name = %s", (host_name,))
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
