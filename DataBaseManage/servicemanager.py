from utils.schema import Service, SimpleRack, SimpleService, SimpleHost
from DataBaseManage.connection import BaseManager
import psycopg2
import psycopg2.extras

# TODO
# 1.Service link user 2.assign ip

class ServiceManager(BaseManager):
    """Class for managing service operations"""

    # Service operations
    def createService(
        self, name: str, dc_name: str, n_racks: int, total_ip: int, username: int
    ) -> Service | None:
        """
        Create a new service in the database.

        Args:
            name (str): Name of the service
            dc_name (str): Data center that the service belongs to
            n_racks (rack): Number of racks to assign
            total_ip (int): Number of IP addresses to assign

        Returns:
            Service: A Service object representing the newly created service.
            None: If creation fails
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:

                # Check if datacenter exists
                cursor.execute(
                    "SELECT name FROM datacenters WHERE name = %s", (dc_name,)
                )
                dc_data = cursor.fetchone()
                if dc_data is None:
                    raise Exception(f"Datacenter named {dc_name} does not exist")
                
                # Check if username exists
                cursor.excute(
                    "SELECT username Form users WHERE username = %s", (username,)
                )
                username = cursor.fetchone()
                if username is None:
                    raise Exception(f"User named {username} does not exist")
                
                # Insert the new service
                cursor.execute(
                    """
                    INSERT INTO services (name, total_ip, dc_name, username)
                    VALUES (%s, %s, %s, %s)
                    RETURNING name
                    """,
                    (name, total_ip, dc_data["name"], username),
                )

                # Get the newly created service data
                new_service = cursor.fetchone()

                if not new_service:
                    conn.rollback()
                    return None

                service_id = new_service["id"]

                # Find {n_racks} racks that are not assigned to any service
                cursor.execute(
                    """
                    SELECT name FROM racks 
                    WHERE service_name IS NULL
                    LIMIT %s
                    """,
                    (n_racks,),
                )
                racks_data = cursor.fetchall()

                if racks_data is None:
                    raise Exception(f"No available racks to assign to service {name}")

                if racks_data.__len__() < n_racks:
                    raise Exception(
                        f"Not enough available racks to assign to service {name}"
                    )

                # Assign racks to the service
                assigned_racks = []
                for rack_data in racks_data:
                    rack_name = rack_data["name"]

                    cursor.execute(
                        """
                        UPDATE racks 
                        SET service_name = %s 
                        WHERE name = %s
                        RETURNING *
                        """,
                        (name, rack_name),
                    )
                    updated_rack = cursor.fetchone()
                     # Get hosts for this rack
                    cursor.execute(
                        "SELECT * FROM hosts WHERE rack_name = %s",
                        (rack_name,),
                    )
                    hosts_data = cursor.fetchall()
                    hosts = [
                        SimpleHost(
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
                    already_used = sum(
                        host.height for host in hosts
                    )
                    # Calculate the remaining capacity
                    capacity = updated_rack["height"] - already_used
                    

                    if updated_rack:
                        assigned_racks.append(
                            SimpleRack(
                                name=updated_rack["name"],
                                height=updated_rack["height"],
                                capacity=capacity,
                                n_hosts=n_hosts,
                                service_name=new_service["name"],
                                room_name=updated_rack["room_name"],
                            )
                        )

                # Get {total_ip} IP addresses in the datacenter
                cursor.execute(
                    """
                    SELECT ip FROM IPs WHERE dc_name = %s AND service_name = NULL LIMIT %s
                    """,
                    (dc_data["name"], total_ip),
                )
                ip_data = cursor.fetchall()
                total_ip_list = [ip["ip"] for ip in ip_data]

                if len(total_ip_list) < total_ip:
                    raise Exception(
                        f"Not enough available IP addresses to assign to service {name}"
                    )

                # Assign service_id to the IP addresses
                for ip in total_ip_list:
                    cursor.execute(
                        """
                        UPDATE IPs 
                        SET service_name = %s 
                        WHERE ip = %s
                        """,
                        (name, ip),
                    )

                # Commit all changes
                conn.commit()

                # Create and return a Service object
                return Service(
                    name=name,
                    allocated_racks=assigned_racks,
                    hosts = hosts,
                    username=username,
                    total_ip_list=total_ip_list,
                    available_ip_list=total_ip_list,
                )

        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    def getService(self, service_name: str) -> Service | None:
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Get the specific service
                cursor.execute("SELECT * FROM services WHERE name = %s", (service_name,))
                data = cursor.fetchone()
                if not data:
                    return None

                # Get racks for this service
                cursor.execute(
                    "SELECT * FROM racks WHERE service_name = %s", (service_name,)
                )
                racks_data = cursor.fetchall()

                # Convert to SimpleRack objects
                racks = []
                for rack_data in racks_data:
                    hosts = []
                    # Get hosts for this rack
                    cursor.execute(
                        "SELECT * FROM hosts WHERE rack_name = %s",
                        (rack_data["name"],),
                    )
                    hosts_data = cursor.fetchall()
                    hosts = [
                        SimpleHost(
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
                    already_used = sum(
                        host.height for host in hosts
                    )
                    # Calculate the remaining capacity
                    capacity = rack_data["height"] - already_used
                    # Create a SimpleRack object
                    racks.append(
                        SimpleRack(
                            name=rack_data["name"],
                            height=rack_data["height"],
                            capacity=capacity,
                            n_hosts=n_hosts,
                            service_name=data["name"],
                            room_name=rack_data["room_name"],
                        )
                    )
                # Calculate the number of hosts
                n_hosts = sum(rack.n_hosts for rack in racks)
                total_ip_list = []
                available_ip_list = []
                # Get IP addresses for this service
                cursor.execute(
                    "SELECT ip FROM IPs WHERE service_name = %s", (service_name,)
                )
                ip_data = cursor.fetchall()
                for ip in ip_data:
                    total_ip_list.append(ip["ip"])
                cursor.execute(
                    "SELECT ip FROM IPs WHERE service_name = %s AND assigned = TRUE",
                    (service_name,),
                )
                ip_data = cursor.fetchall()
                for ip in ip_data:
                    available_ip_list.append(ip["ip"])
                
                # Create and return a Service object
                return Service(
                    name=data["name"],
                    hosts=hosts,
                    username=data["username"],
                    allocated_racks=racks,
                    allocated_subnet=data["subnet"],  
                    total_ip_list=total_ip_list,
                    available_ip_list=available_ip_list,
                )

        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    def getAllServices(self) -> list[Service]:
        """
        Get all services from the database.

        Returns:
            list[Service]: List of all Service objects
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("SELECT name FROM services")
                services_data = cursor.fetchall()

                service_list = []
                for data in services_data:
                    service_name = data["name"]
                    service = self.getService(service_name)
                    if service:
                        service_list.append(service)

                return service_list

        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    def updateService(self, old_name, new_name=None, racks=None, ip_list=None):
        """
        Update an existing service in the database.

        Args:
            old_name (str): Old name of the service to update
            new_name (str, optional): New name for the service
            racks (list[SimpleRack], optional): New racks to assign to this service
            ip_list (list[str], optional): New IP addresses to assign to this service

        Returns:
            Service: Updated Service object
            None: If service not found or update fails
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # First check if service exists
                cursor.execute("SELECT * FROM services WHERE name = %s", (old_name,))
                service = cursor.fetchone()
                if not service:
                    return None

                # Prepare update query parts
                update_parts = []
                params = []

                if new_name is not None:
                    update_parts.append("name = %s")
                    params.append(new_name)

                # Handle racks if provided
                if racks is not None:
                    # First, unassign all racks from this service
                    cursor.execute(
                        "UPDATE racks SET service_name = NULL WHERE name = %s",
                        (old_name,),
                    )

                    # Then assign provided racks to this service
                    for rack in racks:
                        cursor.execute(
                            "UPDATE racks SET service_name = %s WHERE name = %s",
                            (new_name, rack.name),
                        )

                # Handle IP addresses if provided
                if ip_list is not None:
                    # First, delete all existing IP addresses for this service
                    cursor.execute(
                        "DELETE FROM IPs WHERE service_name = %s", (old_name,)
                    )

                    # Then add new IP addresses
                    for ip in ip_list:
                        cursor.execute(
                            "INSERT INTO IPs (service_name, ip) VALUES (%s, %s)",
                            (new_name, ip),
                        )

                # Update the service if there are changes
                if update_parts:
                    # Add updated_at to be updated
                    update_parts.append("updated_at = CURRENT_TIMESTAMP")

                    # Build and execute update query
                    query = f"UPDATE services SET {', '.join(update_parts)} WHERE name = %s RETURNING *"
                    params.append(old_name)

                    cursor.execute(query, params)
                    updated_service = cursor.fetchone()
                else:
                    updated_service = service

                # Get updated racks for this service
                cursor.execute(
                    "SELECT * FROM racks WHERE service_name = %s", (new_name,)
                )
                racks_data = cursor.fetchall()
                # Get capacity and n_hosts for each rack
                updated_racks = []
                for rack_data in racks_data:
                    # Get hosts for this rack
                    cursor.execute(
                        "SELECT * FROM hosts WHERE rack_name = %s",
                        (rack_data["name"],),
                    )
                    hosts_data = cursor.fetchall()
                    hosts = [
                        SimpleHost(
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
                    already_used = sum(
                        host.height for host in hosts
                    )
                    # Calculate the remaining capacity
                    capacity = rack_data["height"] - already_used
                    # Create a SimpleRack object
                    rack = SimpleRack(
                        name=rack_data["name"],
                        height=rack_data["height"],
                        capacity=capacity,
                        n_hosts=n_hosts,
                        service_name=updated_service["name"],
                        room_name=rack_data["room_name"],
                    )
                    updated_racks.append(rack)

                # Get updated IP addresses for this service
                cursor.execute(
                    "SELECT ip FROM IPs WHERE service_name = %s", (new_name,)
                )
                ip_data = cursor.fetchall()
                updated_ip_list = [ip["ip"] for ip in ip_data]

                # Commit all changes
                conn.commit()

                # Create and return updated Service object
                return Service(
                    name=updated_service["name"],
                    allocated_racks=updated_racks,
                    hosts=hosts,
                    username=updated_service["username"],
                    allocated_subnet=updated_service["subnet"],
                    total_ip_list=updated_ip_list,
                    available_ip_list=updated_ip_list,
                )

        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    def deleteService(self, service_name: str) -> bool:
        """
        Delete a service from the database.

        Args:
            service_name (str): Name of the service to delete

        Returns:
            bool: True if service was successfully deleted, False if not found
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                # First check if service exists
                cursor.execute("SELECT id FROM services WHERE name = %s", (service_name,))
                if cursor.fetchone() is None:
                    return False

                # Unassign racks from this service (set service_id to NULL)
                cursor.execute(
                    "UPDATE racks SET service_name = NULL WHERE service_name = %s",
                    (service_name,),
                )

                # Delete IP addresses for this service
                cursor.execute(
                    "DELETE FROM IPs WHERE service_name = %s", (service_name,)
                )

                # Delete the service
                cursor.execute("DELETE FROM services WHERE name = %s", (service_name,))

                # Commit all changes
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

    def assignRackToService(self, service_name: str, rack_name: str) -> bool:
        """
        Assign a rack to a service.

        Args:
            service_name (str): Name of the service
            rack_name (str): Name of the rack to assign

        Returns:
            bool: True if assignment was successful, False otherwise
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                # Check if service exists
                cursor.execute("SELECT name FROM services WHERE name = %s", (service_name,))
                result = cursor.fetchone()
                if result is None:
                    return False

                # Check if rack exists
                cursor.execute("SELECT name FROM racks WHERE name = %s", (rack_name,))
                result = cursor.fetchone()
                if result is None:
                    return False

                rack_name = result[0]
                # Get the service_name
                cursor.execute(
                    "SELECT name FROM services WHERE name = %s", (service_name,)
                )
                result = cursor.fetchone()
                if result is None:
                    return False
                service_name = result[0]
                # Check if the rack is already assigned to a service
                cursor.execute(
                    "SELECT service_name FROM racks WHERE name = %s", (rack_name,)
                )
                result = cursor.fetchone()
                if result is not None and result[0] is not None:
                    # Rack is already assigned to a service
                    return False
                # Assign the rack to the service
                cursor.execute(
                    "UPDATE racks SET service_name = %s WHERE name = %s",
                    (service_name, rack_name),
                )
                
                if cursor.rowcount <= 0:
                    return False

                # Commit changes
                conn.commit()

                return True

        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    def unassignRackFromService(self, rack_name: str) -> bool:
        """
        Unassign a rack from any service.

        Args:
            rack_name (str): Name of the rack to unassign

        Returns:
            bool: True if unassignment was successful, False otherwise
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                # Get the current service_id before unassigning
                cursor.execute("SELECT name FROM racks WHERE name = %s", (rack_name,))
                result = cursor.fetchone()
                if result is None:
                    return False

                rack_name = result[0]
                cursor.execute("SELECT service_name FROM racks WHERE name = %s", (rack_name,))
                result = cursor.fetchone()
                if result is None:
                    return False

                service_name = result[0]
                if service_name is None:
                    # Rack is not assigned to any service
                    return True

                # Unassign rack
                cursor.execute(
                    "UPDATE racks SET service_name = NULL WHERE name = %s", (rack_name,)
                )

                if cursor.rowcount <= 0:
                    return False

                # Commit changes
                conn.commit()

                return True

        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    def addIPToService(self, service_name, ip_address):
        """
        Add an IP address to a service.

        Args:
            service_name (str): Name of the service
            ip_address (str): IP address to add

        Returns:
            bool: True if addition was successful, False otherwise
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                # Check if service exists
                cursor.execute("SELECT name FROM services WHERE name = %s", (service_name,))
                if cursor.fetchone() is None:
                    return False

                # Add IP address
                cursor.execute(
                    "INSERT INTO IPs (service_name, ip) VALUES (%s, %s)",
                    (service_name, ip_address),
                )

                # Update service IP count
                cursor.execute(
                    """
                    UPDATE services 
                    SET total_ip = (SELECT COUNT(*) FROM service_ips WHERE service_name = %s)
                    """,
                    (service_name),
                )

                # Commit changes
                conn.commit()

                return True

        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    def removeIPFromService(self, service_name, ip_address):
        """
        Remove an IP address from a service.

        Args:
            service_name (str): Name of the service
            ip_address (str): IP address to remove

        Returns:
            bool: True if removal was successful, False otherwise
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                # Delete IP address
                cursor.execute(
                    "DELETE FROM IPs WHERE service_name = %s AND ip = %s",
                    (service_name, ip_address),
                )

                if cursor.rowcount <= 0:
                    return False

                # Update service IP count
                cursor.execute(
                    """
                    UPDATE services 
                    SET total_ip = (SELECT COUNT(*) FROM IPs WHERE service_name = %s)
                    """,
                    (service_name),
                )

                # Commit changes
                conn.commit()

                return True

        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)

