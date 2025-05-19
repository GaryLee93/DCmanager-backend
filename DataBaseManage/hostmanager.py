import os
from utils.schema import IP_Range, DataCenter, Room, Rack, Host, Service, User
from utils.schema import (
    SimpleRoom,
    SimpleRack,
    SimpleHost,
    SimpleService,
    SimpleDataCenter,
)
from DataBaseManage.connection import BaseManager


class HostManager(BaseManager):

    # CREATE operations
    def createHost(self, name, height, ip, rack_id, service_id=None, pos=None):
        """
        Create a new host in a rack.

        Args:
            name (str): Name of the host
            height (int): Height of the host in rack units
            ip (str): IP address of the host
            rack_id (str): ID of the rack this host belongs to
            service_id (str, optional): ID of the service this host is assigned to
            pos (int, optional): Position in the rack. If None, will use the next available position.

        Returns:
            str: ID of the newly created host
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                # Check if rack exists and get its room_id and datacenter_id
                cursor.execute(
                    "SELECT id, room_id, dc_id FROM racks WHERE id = %s", (rack_id,)
                )
                rack_info = cursor.fetchone()

                if rack_info is None:
                    raise Exception(f"Rack with ID {rack_id} does not exist")

                room_id = rack_info[1]
                datacenter_id = rack_info[2]

                # Check if service exists (if provided)
                if service_id is not None:
                    cursor.execute(
                        "SELECT id FROM services WHERE id = %s", (service_id,)
                    )
                    if cursor.fetchone() is None:
                        raise Exception(f"Service with ID {service_id} does not exist")

                # Check if IP address is unique
                cursor.execute("SELECT id FROM hosts WHERE ip = %s", (ip,))
                if cursor.fetchone() is not None:
                    raise Exception(f"Host with IP {ip} already exists")

                # Generate a new UUID for the host
                cursor.execute("SELECT gen_random_uuid()")
                host_id = cursor.fetchone()[0]

                # Calculate position if not provided
                if pos is None:
                    cursor.execute(
                        "SELECT COALESCE(MAX(pos), 0) + 1 FROM hosts WHERE rack_id = %s",
                        (rack_id,),
                    )
                    pos = cursor.fetchone()[0]

                # Insert host
                cursor.execute(
                    "INSERT INTO hosts (id, name, height, ip, service_id, dc_id, room_id, rack_id, pos) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (
                        host_id,
                        name,
                        height,
                        ip,
                        service_id,
                        datacenter_id,
                        room_id,
                        rack_id,
                        pos,
                    ),
                )

                # Update the host count in the rack
                cursor.execute(
                    "UPDATE racks SET n_hosts = n_hosts + 1 WHERE id = %s", (rack_id,)
                )

                # Update the host count in the room
                cursor.execute(
                    "UPDATE rooms SET n_hosts = n_hosts + 1 WHERE id = %s", (room_id,)
                )

                # Update the host count in the datacenter
                cursor.execute(
                    "UPDATE datacenters SET n_hosts = n_hosts + 1 WHERE id = %s",
                    (datacenter_id,),
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
    def getHost(self, host_id):
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
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, name, height, ip, service_id, dc_id, room_id, rack_id FROM hosts WHERE id = %s",
                    (host_id,),
                )
                result = cursor.fetchone()

                if result is None:
                    return None

                # Create and return the Host object
                return Host(
                    id=result[0],
                    name=result[1],
                    height=result[2],
                    ip=result[3],
                    service_id=result[4],
                    dc_id=result[5],
                    room_id=result[6],
                    rack_id=result[7],
                )

        except Exception as e:
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    def getHostByIP(self, ip):
        """
        Get a host by IP address.

        Args:
            ip (str): IP address of the host to retrieve

        Returns:
            Host: Host object if found, None otherwise
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, name, height, ip, service_id, dc_id, room_id, rack_id FROM hosts WHERE ip = %s",
                    (ip,),
                )
                result = cursor.fetchone()

                if result is None:
                    return None

                # Create and return the Host object
                return Host(
                    id=result[0],
                    name=result[1],
                    height=result[2],
                    ip=result[3],
                    service_id=result[4],
                    dc_id=result[5],
                    room_id=result[6],
                    rack_id=result[7],
                )

        except Exception as e:
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    # UPDATE operations
    def updateHost(
        self, host_id, name=None, height=None, ip=None, service_id=None, rack_id=None
    ):
        """
        Update a host's information.

        Args:
            host_id (str): ID of the host to update
            name (str, optional): New name for the host
            height (int, optional): New height for the host
            ip (str, optional): New IP address for the host
            service_id (str, optional): New service ID for the host
            rack_id (str, optional): New rack ID for the host

        Returns:
            bool: True if host was successfully updated, False if not found
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                # First check if host exists and get its current information
                cursor.execute(
                    "SELECT id, rack_id, room_id, dc_id FROM hosts WHERE id = %s",
                    (host_id,),
                )
                host_info = cursor.fetchone()

                if host_info is None:
                    return False

                current_rack_id = host_info[1]
                current_room_id = host_info[2]
                current_datacenter_id = host_info[3]

                # Check if IP is unique if changing it
                if ip is not None:
                    cursor.execute(
                        "SELECT id FROM hosts WHERE ip = %s AND id != %s", (ip, host_id)
                    )
                    if cursor.fetchone() is not None:
                        raise Exception(f"Host with IP {ip} already exists")

                # Check if rack exists and get its room_id and datacenter_id if changing rack
                new_room_id = current_room_id
                new_datacenter_id = current_datacenter_id

                if rack_id is not None and rack_id != current_rack_id:
                    cursor.execute(
                        "SELECT id, room_id, dc_id FROM racks WHERE id = %s", (rack_id,)
                    )
                    rack_info = cursor.fetchone()

                    if rack_info is None:
                        raise Exception(f"Rack with ID {rack_id} does not exist")

                    new_room_id = rack_info[1]
                    new_datacenter_id = rack_info[2]

                # Check if service exists (if a new one is provided)
                if service_id is not None:
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

                if ip is not None:
                    query_parts.append("ip = %s")
                    update_params.append(ip)

                if service_id is not None:
                    query_parts.append("service_id = %s")
                    update_params.append(service_id)

                if rack_id is not None:
                    query_parts.append("rack_id = %s")
                    update_params.append(rack_id)
                    query_parts.append("room_id = %s")
                    update_params.append(new_room_id)
                    query_parts.append("dc_id = %s")
                    update_params.append(new_datacenter_id)

                if not query_parts:
                    # Nothing to update
                    return True

                query = f"UPDATE hosts SET {', '.join(query_parts)} WHERE id = %s"
                update_params.append(host_id)

                cursor.execute(query, tuple(update_params))

                # Update counts if rack, room, or datacenter has changed
                if rack_id is not None and rack_id != current_rack_id:
                    # Decrement host count in old rack, room, and datacenter
                    cursor.execute(
                        "UPDATE racks SET n_hosts = n_hosts - 1 WHERE id = %s",
                        (current_rack_id,),
                    )
                    cursor.execute(
                        "UPDATE rooms SET n_hosts = n_hosts - 1 WHERE id = %s",
                        (current_room_id,),
                    )
                    cursor.execute(
                        "UPDATE datacenters SET n_hosts = n_hosts - 1 WHERE id = %s",
                        (current_datacenter_id,),
                    )

                    # Increment host count in new rack, room, and datacenter
                    cursor.execute(
                        "UPDATE racks SET n_hosts = n_hosts + 1 WHERE id = %s",
                        (rack_id,),
                    )
                    cursor.execute(
                        "UPDATE rooms SET n_hosts = n_hosts + 1 WHERE id = %s",
                        (new_room_id,),
                    )
                    cursor.execute(
                        "UPDATE datacenters SET n_hosts = n_hosts + 1 WHERE id = %s",
                        (new_datacenter_id,),
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

    # DELETE operations
    def deleteHost(self, host_id):
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
            with conn.cursor() as cursor:
                # First check if host exists and get its rack_id, room_id, and datacenter_id
                cursor.execute(
                    "SELECT id, rack_id, room_id, dc_id FROM hosts WHERE id = %s",
                    (host_id,),
                )
                host_info = cursor.fetchone()

                if host_info is None:
                    return False

                rack_id = host_info[1]
                room_id = host_info[2]
                datacenter_id = host_info[3]

                # Delete the host
                cursor.execute("DELETE FROM hosts WHERE id = %s", (host_id,))

                # Update the host count in the rack
                cursor.execute(
                    "UPDATE racks SET n_hosts = n_hosts - 1 WHERE id = %s", (rack_id,)
                )

                # Update the host count in the room
                cursor.execute(
                    "UPDATE rooms SET n_hosts = n_hosts - 1 WHERE id = %s", (room_id,)
                )

                # Update the host count in the datacenter
                cursor.execute(
                    "UPDATE datacenters SET n_hosts = n_hosts - 1 WHERE id = %s",
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
