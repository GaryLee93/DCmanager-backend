from utils.schema import Host
from DataBaseManage.connection import BaseManager
from psycopg2.extras import RealDictCursor


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
                    "SELECT id, name, room_id, room_name, dc_id, dc_name, service_id, service_name FROM racks WHERE name = %s",
                    (rack_name,),
                )
                rack_data = cursor.fetchone()

                if rack_data is None:
                    raise Exception(f"Rack with Name {rack_name} does not exist")

                # Get an available IP of service
                cursor.execute(
                    "SELECT ip FROM service_ips WHERE service_id = %s AND assigned = FALSE LIMIT 1",
                    (rack_data["service_id"],),
                )
                allocated_ip = cursor.fetchone()["ip"] if cursor.rowcount > 0 else None

                if allocated_ip is not None:
                    # Update the IP to be assigned and Decrease the available IP count
                    cursor.execute(
                        "UPDATE service_ips SET assigned = TRUE WHERE ip = %s",
                        (allocated_ip,),
                    )
                    cursor.execute(
                        "UPDATE services SET available_ip = available_ip - 1 WHERE id = %s",
                        (rack_data["service_id"],),
                    )

                # Generate a new UUID for the host
                cursor.execute("SELECT gen_random_uuid()")
                host_id = cursor.fetchone()["gen_random_uuid"]

                # Insert host
                cursor.execute(
                    "INSERT INTO hosts (id, name, height, ip, service_id, service_name, dc_id, dc_name, room_id, room_name, rack_id, rack_name, pos) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (
                        host_id,
                        name,
                        height,
                        allocated_ip,
                        rack_data["service_id"],
                        rack_data["service_name"],
                        rack_data["dc_id"],
                        rack_data["dc_name"],
                        rack_data["room_id"],
                        rack_data["room_name"],
                        rack_data["id"],
                        rack_data["name"],
                        pos,
                    ),
                )
                conn.commit()
                return host_id

        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    # READ operations
    def getHost(self, host_id: str) -> Host | None:
        """
        Get a host by ID.

        Args:
            host_id (str): ID of the host to retrieve

        Returns:
            Host: Host object if found, None otherwise
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT * FROM hosts WHERE id = %s",
                    (host_id,),
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
        host_id: str,
        name: str | None = None,
        height: int | None = None,
        running: bool | None = None,
        rack_id=None,
    ):
        """
        Update a host's information.

        Args:
            host_id (str): ID of the host to update
            name (str, optional): New name for the host
            height (int, optional): New height for the host
            running (bool, optional): New running status for the host
            rack_id (str, optional): New rack ID for the host.
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
                    "SELECT id, rack_id, room_id, dc_id, service_id FROM hosts WHERE id = %s",
                    (host_id,),
                )
                host_data = cursor.fetchone()

                if host_data is None:
                    return False

                current_rack_id = host_data["rack_id"]
                current_room_id = host_data["room_id"]
                current_datacenter_id = host_data["dc_id"]
                current_service_id = host_data["service_id"]

                # Check if rack exists and get its room_id and datacenter_id if changing rack
                new_rack_data = None
                if rack_id is not None and rack_id != current_rack_id:
                    cursor.execute(
                        "SELECT id, name, room_id, room_name, dc_id, service_id FROM racks WHERE id = %s",
                        (rack_id,),
                    )
                    new_rack_data = cursor.fetchone()

                    if new_rack_data is None:
                        raise Exception(f"Rack with ID {rack_id} does not exist")

                    if (
                        new_rack_data["service_id"] != current_service_id
                        or new_rack_data["dc_id"] != current_datacenter_id
                    ):
                        raise Exception(
                            f"Cannot move host to rack in different service or datacenter"
                        )

                # Build the update query based on provided parameters
                update_params = []
                query_parts = []

                if name is not None:
                    query_parts.append("name = %s")
                    update_params.append(name)

                if height is not None:
                    query_parts.append("height = %s")
                    update_params.append(height)

                if running is not None:
                    query_parts.append("running = %s")
                    update_params.append(running)

                if new_rack_data is not None:
                    query_parts.append("rack_id = %s")
                    update_params.append(new_rack_data["id"])
                    query_parts.append("rack_name = %s")
                    update_params.append(new_rack_data["name"])

                    if new_rack_data["room_id"] != current_room_id:
                        query_parts.append("room_id = %s")
                        update_params.append(new_rack_data["room_id"])
                        query_parts.append("room_name = %s")
                        update_params.append(new_rack_data["room_name"])

                if not query_parts:
                    # Nothing to update
                    return True

                query = f"UPDATE hosts SET {', '.join(query_parts)} WHERE id = %s"
                update_params.append(host_id)

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
    def deleteHost(self, host_id: str) -> bool:
        """
        Delete a host from the database.

        Args:
            host_id (str): ID of the host to delete

        Returns:
            bool: True if host was successfully deleted, False if not found
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # First check if host exists and get its rack_id, room_id, and datacenter_id
                cursor.execute(
                    "SELECT id, rack_id, room_id, dc_id FROM hosts WHERE id = %s",
                    (host_id,),
                )
                host_data = cursor.fetchone()

                if host_data is None:
                    return False

                rack_id = host_data["rack_id"]
                room_id = host_data["room_id"]
                datacenter_id = host_data["dc_id"]

                # Delete the host
                cursor.execute("DELETE FROM hosts WHERE id = %s", (host_id,))
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
