from utils.schema import Service, SimpleRack, SimpleService, Host
from DataBaseManage.connection import BaseManager
import psycopg2
import psycopg2.extras

class ServiceManager(BaseManager):
    """Class for managing service operations"""

    # Service operations
    def createService(
        self, name: str, n_allocated_racks: dict[str, int], allocated_subnet: str, username: str
    ) -> Service | None:
        """
        Create a new service in the database.

        Args:
            name (str): Name of the service
            n_allocated_racks (dict[str, int]): Number of racks to allocate in each data center
            allocated_subnet (str): Subnet allocated to the service
            username (str): Username of the user creating the service

        Returns:
            Service: A Service object representing the newly created service.
            None: If creation fails
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Check if username exists
                cursor.execute(
                    "SELECT username FROM users WHERE username = %s", (username,)
                )
                user_data = cursor.fetchone()
                if user_data is None:
                    raise Exception(f"User {username} does not exist")

                # Insert the new service
                cursor.execute(
                    """
                    INSERT INTO services (name, subnet, username)
                    VALUES (%s, %s, %s)
                    RETURNING name
                    """,
                    (name, allocated_subnet, username),
                )

                # Get the newly created service data
                new_service = cursor.fetchone()

                if not new_service:
                    conn.rollback()
                    return None

                # Process allocated racks for each datacenter
                all_assigned_racks = {}
                all_hosts = []
                all_ip_addresses = []

                for dc_name, n_racks in n_allocated_racks.items():
                    # Check if datacenter exists
                    cursor.execute(
                        "SELECT name FROM datacenters WHERE name = %s", (dc_name,)
                    )
                    dc_data = cursor.fetchone()
                    if dc_data is None:
                        raise Exception(f"Datacenter named {dc_name} does not exist")

                    # Find {n_racks} racks that are not assigned to any service in this DC
                    cursor.execute(
                        """
                        SELECT name FROM racks 
                        WHERE service_name IS NULL AND dc_name = %s
                        LIMIT %s
                        """,
                        (dc_name, n_racks),
                    )
                    racks_data = cursor.fetchall()

                    if len(racks_data) < n_racks:
                        raise Exception(
                            f"Not enough available racks in datacenter {dc_name} to assign to service {name}"
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
                        rack_hosts = [
                            Host(
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
                        all_hosts.extend(rack_hosts)
                        
                        # Calculate the number of hosts
                        n_hosts = len(rack_hosts)
                        # Calculate the capacity
                        already_used = sum(host.height for host in rack_hosts)
                        # Calculate the remaining capacity
                        capacity = updated_rack["height"] - already_used

                        if updated_rack:
                            assigned_racks.append(
                                SimpleRack(
                                    name=updated_rack["name"],
                                    height=updated_rack["height"],
                                    capacity=capacity,
                                    n_hosts=n_hosts,
                                    service_name=name,
                                    room_name=updated_rack["room_name"],
                                )
                            )
                    
                    # Store the racks for this datacenter
                    all_assigned_racks[dc_name] = assigned_racks

                    # Get available IP addresses in this datacenter for the subnet
                    cursor.execute(
                        """
                        SELECT ip FROM IPs 
                        WHERE dc_name = %s AND service_name IS NULL
                        LIMIT %s
                        """,
                        (dc_name, n_racks * 10),  # Allocate some IPs per rack as an example
                    )
                    ip_data = cursor.fetchall()
                    dc_ips = [ip["ip"] for ip in ip_data]
                    all_ip_addresses.extend(dc_ips)

                    # Assign service name to the IP addresses
                    for ip in dc_ips:
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
                    allocated_racks=all_assigned_racks,
                    hosts=all_hosts,
                    username=username,
                    allocated_subnet=allocated_subnet,
                    total_ip_list=all_ip_addresses,
                    available_ip_list=all_ip_addresses.copy(),
                )

        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    def getService(self, service_name: str) -> Service | None:
        """
        Get a service from the database.

        Args:
            service_name (str): Name of the service

        Returns:
            Service: Service object if found
            None: If service not found
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Get the specific service
                cursor.execute(
                    "SELECT * FROM services WHERE name = %s", (service_name,)
                )
                data = cursor.fetchone()
                if not data:
                    return None

                # Get all datacenters that have racks for this service
                cursor.execute(
                    """
                    SELECT DISTINCT dc_name 
                    FROM racks 
                    WHERE service_name = %s
                    """, 
                    (service_name,)
                )
                dc_data = cursor.fetchall()
                dc_names = [dc["dc_name"] for dc in dc_data]
                
                # Initialize allocated_racks dictionary
                allocated_racks = {dc_name: [] for dc_name in dc_names}
                all_hosts = []
                
                # For each datacenter, get the racks
                for dc_name in dc_names:
                    cursor.execute(
                        """
                        SELECT * FROM racks 
                        WHERE service_name = %s AND dc_name = %s
                        """, 
                        (service_name, dc_name)
                    )
                    racks_data = cursor.fetchall()
                    
                    # Process each rack in this datacenter
                    for rack_data in racks_data:
                        # Get hosts for this rack
                        cursor.execute(
                            "SELECT * FROM hosts WHERE rack_name = %s",
                            (rack_data["name"],),
                        )
                        hosts_data = cursor.fetchall()
                        rack_hosts = [
                            Host(
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
                        all_hosts.extend(rack_hosts)
                        
                        # Calculate the capacity
                        already_used = sum(host.height for host in rack_hosts)
                        capacity = rack_data["height"] - already_used
                        
                        # Create a SimpleRack object
                        allocated_racks[dc_name].append(
                            SimpleRack(
                                name=rack_data["name"],
                                height=rack_data["height"],
                                capacity=capacity,
                                n_hosts=len(rack_hosts),
                                service_name=service_name,
                                room_name=rack_data["room_name"],
                            )
                        )

                # Get all IP addresses for this service
                cursor.execute(
                    "SELECT ip FROM IPs WHERE service_name = %s", 
                    (service_name,)
                )
                ip_data = cursor.fetchall()
                total_ip_list = [ip["ip"] for ip in ip_data]
                
                # Get available (not assigned) IP addresses for this service
                cursor.execute(
                    """
                    SELECT ip FROM IPs 
                    WHERE service_name = %s AND assigned = FALSE
                    """,
                    (service_name,),
                )
                available_ip_data = cursor.fetchall()
                available_ip_list = [ip["ip"] for ip in available_ip_data]

                # Create and return a Service object
                return Service(
                    name=data["name"],
                    allocated_racks=allocated_racks,
                    hosts=all_hosts,
                    username=data["username"],
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

    def getAllServices(self) -> list[SimpleService]:
        """
        Get all services from the database.

        Returns:
            list[SimpleService]: List of all SimpleService objects
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT s.name, s.subnet, s.username, 
                           COUNT(DISTINCT r.name) as rack_count,
                           COUNT(DISTINCT h.name) as host_count,
                           COUNT(DISTINCT i.ip) as ip_count
                    FROM services s
                    LEFT JOIN racks r ON s.name = r.service_name
                    LEFT JOIN hosts h ON s.name = h.service_name
                    LEFT JOIN IPs i ON s.name = i.service_name
                    GROUP BY s.name, s.subnet, s.username
                """)
                services_data = cursor.fetchall()

                service_list = []
                for data in services_data:
                    # Create a SimpleService object with summary information
                    service_list.append(
                        SimpleService(
                            name=data["name"],
                            username=data["username"],
                            allocated_subnet=data["subnet"],
                            rack_count=data["rack_count"],
                            host_count=data["host_count"],
                            ip_count=data["ip_count"]
                        )
                    )

                return service_list

        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    def updateService(
        self, 
        service_name: str, 
        new_name: str | None = None, 
        new_n_allocated_racks: dict[str, int] | None = None, 
        new_allocated_subnet: str | None = None
    ) -> Service | None:
        """
        Update an existing service in the database.

        Args:
            service_name (str): Name of the service to update
            new_name (str | None): New name for the service
            new_n_allocated_racks (dict[str, int] | None): New number of racks to allocate in each data center
                e.g. {"DC1": 2, "DC2": 3} means to add 2 racks in DC1 and 3 racks in DC2
            new_allocated_subnet (str | None): New subnet allocated to the service

        Returns:
            Service: Updated Service object
            None: If service not found or update fails
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # First check if service exists
                cursor.execute("SELECT * FROM services WHERE name = %s", (service_name,))
                service = cursor.fetchone()
                if not service:
                    return None

                update_name = new_name if new_name else service_name
                update_subnet = new_allocated_subnet if new_allocated_subnet else service["subnet"]

                # Prepare update query parts for service table
                update_parts = []
                params = []

                if new_name is not None:
                    update_parts.append("name = %s")
                    params.append(new_name)

                if new_allocated_subnet is not None:
                    update_parts.append("subnet = %s")
                    params.append(new_allocated_subnet)

                # Update the service record if there are changes
                if update_parts:
                    # Add updated_at to be updated
                    update_parts.append("updated_at = CURRENT_TIMESTAMP")

                    # Build and execute update query
                    query = f"UPDATE services SET {', '.join(update_parts)} WHERE name = %s RETURNING *"
                    params.append(service_name)

                    cursor.execute(query, params)
                    updated_service = cursor.fetchone()
                    
                    # If name was updated, update all references
                    if new_name is not None:
                        # Update service_name in racks table
                        cursor.execute(
                            "UPDATE racks SET service_name = %s WHERE service_name = %s",
                            (new_name, service_name)
                        )
                        
                        # Update service_name in hosts table
                        cursor.execute(
                            "UPDATE hosts SET service_name = %s WHERE service_name = %s",
                            (new_name, service_name)
                        )
                        
                        # Update service_name in IPs table
                        cursor.execute(
                            "UPDATE IPs SET service_name = %s WHERE service_name = %s",
                            (new_name, service_name)
                        )
                else:
                    updated_service = service

                # Handle new rack allocations if provided
                if new_n_allocated_racks is not None:
                    for dc_name, n_racks in new_n_allocated_racks.items():
                        # Verify datacenter exists
                        cursor.execute(
                            "SELECT name FROM datacenters WHERE name = %s", 
                            (dc_name,)
                        )
                        if cursor.fetchone() is None:
                            raise Exception(f"Datacenter {dc_name} does not exist")
                        
                        # Find available racks in this datacenter
                        cursor.execute(
                            """
                            SELECT name FROM racks 
                            WHERE service_name IS NULL AND dc_name = %s
                            LIMIT %s
                            """,
                            (dc_name, n_racks)
                        )
                        available_racks = cursor.fetchall()
                        
                        if len(available_racks) < n_racks:
                            raise Exception(f"Not enough available racks in datacenter {dc_name}")
                        
                        # Assign new racks to this service
                        for rack in available_racks:
                            cursor.execute(
                                "UPDATE racks SET service_name = %s WHERE name = %s",
                                (update_name, rack["name"])
                            )

                # Commit all changes
                conn.commit()
                
                # Return the updated service
                return self.getService(update_name)

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
                cursor.execute(
                    "SELECT name FROM services WHERE name = %s", (service_name,)
                )
                if cursor.fetchone() is None:
                    return False

                # Unassign hosts from this service
                cursor.execute(
                    "UPDATE hosts SET service_name = NULL WHERE service_name = %s",
                    (service_name,)
                )

                # Unassign racks from this service
                cursor.execute(
                    "UPDATE racks SET service_name = NULL WHERE service_name = %s",
                    (service_name,)
                )

                # Release IP addresses from this service
                cursor.execute(
                    "UPDATE IPs SET service_name = NULL, assigned = FALSE WHERE service_name = %s",
                    (service_name,)
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
                cursor.execute(
                    "SELECT name FROM services WHERE name = %s", (service_name,)
                )
                if cursor.fetchone() is None:
                    return False

                # Check if rack exists
                cursor.execute("SELECT name FROM racks WHERE name = %s", (rack_name,))
                if cursor.fetchone() is None:
                    return False

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
                # Check if rack exists and is assigned to a service
                cursor.execute(
                    "SELECT service_name FROM racks WHERE name = %s", (rack_name,)
                )
                result = cursor.fetchone()
                if result is None:
                    return False

                service_name = result[0]
                if service_name is None:
                    # Rack is not assigned to any service
                    return True

                # First unassign any hosts in this rack from the service
                cursor.execute(
                    "UPDATE hosts SET service_name = NULL WHERE rack_name = %s AND service_name = %s",
                    (rack_name, service_name)
                )

                # Unassign rack from service
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

    def addIPToService(self, service_name: str, ip_address: str) -> bool:
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
                cursor.execute(
                    "SELECT name FROM services WHERE name = %s", (service_name,)
                )
                if cursor.fetchone() is None:
                    return False

                # Check if IP already exists and is assigned to another service
                cursor.execute(
                    "SELECT service_name FROM IPs WHERE ip = %s", (ip_address,)
                )
                result = cursor.fetchone()
                if result is not None and result[0] is not None and result[0] != service_name:
                    return False

                # Add or update IP address
                cursor.execute(
                    """
                    INSERT INTO IPs (service_name, ip, assigned)
                    VALUES (%s, %s, FALSE)
                    ON CONFLICT (ip) DO UPDATE
                    SET service_name = EXCLUDED.service_name
                    """,
                    (service_name, ip_address)
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

    def removeIPFromService(self, service_name: str, ip_address: str) -> bool:
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
                # Check if the IP belongs to the service
                cursor.execute(
                    "SELECT service_name FROM IPs WHERE ip = %s AND service_name = %s",
                    (ip_address, service_name)
                )
                if cursor.fetchone() is None:
                    return False

                # Check if the IP is assigned to a host
                cursor.execute(
                    "SELECT name FROM hosts WHERE ip = %s", (ip_address,)
                )
                if cursor.fetchone() is not None:
                    # If IP is assigned to a host, just unassign it from the service
                    cursor.execute(
                        "UPDATE IPs SET assigned = FALSE WHERE ip = %s",
                        (ip_address,)
                    )
                else:
                    # If IP is not assigned to a host, release it completely
                    cursor.execute(
                        "UPDATE IPs SET service_name = NULL, assigned = FALSE WHERE ip = %s",
                        (ip_address,)
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

    def assignIPToHost(self, ip_address: str, host_name: str) -> bool:
        """
        Assign an IP address to a host.

        Args:
            ip_address (str): IP address to assign
            host_name (str): Name of the host

        Returns:
            bool: True if assignment was successful, False otherwise
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                # Check if host exists
                cursor.execute(
                    "SELECT service_name FROM hosts WHERE name = %s", (host_name,)
                )
                host_data = cursor.fetchone()
                if host_data is None:
                    return False
                
                service_name = host_data[0]
                
                # Check if IP is available and belongs to the same service
                cursor.execute(
                    """
                    SELECT service_name, assigned 
                    FROM IPs 
                    WHERE ip = %s
                    """,
                    (ip_address,)
                )
                ip_data = cursor.fetchone()
                
                if ip_data is None:
                    return False
                
                if ip_data[0] != service_name:
                    return False
                
                if ip_data[1]:  # IP is already assigned to another host
                    return False
                
                # Assign the IP to the host
                cursor.execute(
                    "UPDATE hosts SET ip = %s WHERE name = %s",
                    (ip_address, host_name)
                )
                
                # Mark the IP as assigned
                cursor.execute(
                    "UPDATE IPs SET assigned = TRUE WHERE ip = %s",
                    (ip_address,)
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