from utils.schema import Host
from DataBaseManage.connection import BaseManager
from psycopg2.extras import RealDictCursor


# Todo
# if ip empty, allocate more ip
class HostManager(BaseManager):

    # CREATE operations
    def createHost(self, name: str, height: int, rack_name: str, pos: int) -> Host:
        """
        Create a new host in a rack.

        Args:
            name (str): Name of the host
            height (int): Height of the host in rack units
            rack_name (str): Name of the rack this host belongs to
            pos (int): Position in the rack. If None, will use the next available position.

        Returns:
            Host: Host object created
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Check if rack exists
                cursor.execute(
                    "SELECT name, service_name, dc_name, room_name FROM racks WHERE name = %s",
                    (rack_name,),
                )
                rack_data = cursor.fetchone()
                if rack_data is None:
                    return None

                # Get an available IP of service
                cursor.execute(
                    "SELECT ip FROM IPs WHERE service_name = %s AND assigned = FALSE ORDER BY ip DESC LIMIT 1",
                    (rack_data["service_name"],),
                )
                allocated_ip = cursor.fetchone()
                if allocated_ip is not None:
                    # Update the IP to be assigned
                    cursor.execute(
                        "UPDATE IPs SET assigned = TRUE WHERE ip = %s",
                        (allocated_ip,),
                    )

                new_host = Host(
                    name=name,
                    height=height,
                    ip=allocated_ip,
                    running=True,
                    service_name=rack_data["service_name"],
                    dc_name=rack_data["dc_name"],
                    room_name=rack_data["room_name"],
                    rack_name=rack_data["name"],
                    pos=pos,
                )

                # Insert host
                cursor.execute(
                    "INSERT INTO hosts (name, height, ip, running, service_name, dc_name, room_name, rack_name, pos) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (
                        new_host.name,
                        new_host.height,
                        new_host.ip,
                        new_host.running,
                        new_host.service_name,
                        new_host.dc_name,
                        new_host.room_name,
                        new_host.rack_name,
                        new_host.pos,
                    ),
                )
                conn.commit()
                
                return new_host

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
                return Host(
                    name=result["name"],
                    height=result["height"],
                    ip=result["ip"],
                    running=result["running"],
                    service_name=result["service_name"],
                    dc_name=result["dc_name"],
                    room_name=result["room_name"],
                    rack_name=result["rack_name"],
                    pos=result["pos"],
                )
        except Exception as e:
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    def getAllHosts(self) -> list[Host]:
        """
        Get all hosts.

        Args:
            None

        Returns:
            list[Host]: List of all Host objects
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM hosts ORDER BY name")
                results = cursor.fetchall()
                hosts = []
                for result in results:
                    hosts.append(Host(
                        name=result["name"],
                        height=result["height"],
                        ip=result["ip"],
                        running=result["running"],
                        service_name=result["service_name"],
                        dc_name=result["dc_name"],
                        room_name=result["room_name"],
                        rack_name=result["rack_name"],
                        pos=result["pos"],
                    ))
                return hosts



        except Exception as e:
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    # UPDATE operations
    def updateHost(
        self,
        host_name: str,
        new_name: str | None = None,
        new_height: int | None = None,
        new_running: bool | None = None,
        new_rack_name: str | None = None,
        new_pos: int | None = None,
    ) -> bool:
        """
        Update a host's information.

        Args:
            host_name (str): Current name of the host
            new_name (str, optional): New name for the host
            new_height (int, optional): New height for the host
            new_running (bool, optional): New running status for the host
            new_rack_name (str, optional): New rack name for the host. Should be provide with pos.
            new_pos (int, optional): New position for the host in the rack.

        Returns:
            bool
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # First check if host exists and get its current information
                cursor.execute(
                    "SELECT name, rack_name, room_name FROM hosts WHERE name = %s",
                    (host_name,),
                )
                host_data = cursor.fetchone()

                if host_data is None:
                    return False

                current_rack_name = host_data["rack_name"]
                current_room_name = host_data["room_name"]

                # Check if rack to be move to exists
                new_room_name = None
                if new_rack_name is not None and new_rack_name != current_rack_name:
                    cursor.execute(
                        "SELECT name, room_name FROM racks WHERE name = %s",
                        (new_rack_name,),
                    )
                    new_rack_data = cursor.fetchone()

                    if new_rack_data is None:
                        return False

                    new_room_name = new_rack_data["room_name"]

                # Build the update query based on provided parameters
                update_params = []
                query_parts = []

                if new_name is not None:
                    query_parts.append("name = %s")
                    update_params.append(new_name)

                if new_height is not None:
                    query_parts.append("height = %s")
                    update_params.append(new_height)

                if new_running is not None:
                    query_parts.append("running = %s")
                    update_params.append(new_running)

                if new_rack_name is not None:
                    query_parts.append("rack_name = %s")
                    update_params.append(new_rack_name)

                    if new_room_name != current_room_name:
                        query_parts.append("room_name = %s")
                        update_params.append(new_room_name)

                if not query_parts:
                    # Nothing to update
                    return True

                query = f"UPDATE hosts SET {', '.join(query_parts)} WHERE name = %s"
                update_params.append(host_name)

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
                # First check if host exists
                cursor.execute(
                    "SELECT name, rack_name, room_name, dc_name FROM hosts WHERE name = %s",
                    (host_name,),
                )
                host_data = cursor.fetchone()

                if host_data is None:
                    return False

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
