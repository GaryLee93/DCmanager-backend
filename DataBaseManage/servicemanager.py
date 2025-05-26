from utils.schema import Service, SimpleRack, SimpleService, Host
from DataBaseManage.connection import BaseManager
import psycopg2
import psycopg2.extras
import ipaddress

class ServiceManager(BaseManager):
    """Class for managing service operations"""
    def subnet_to_iplist(self, subnet: str) -> list[str]:
        """
        Convert a subnet to a list of IP addresses.

        Args:
            subnet (str): Subnet in CIDR notation
                e.g. 168.0.0/24

        Returns:
            list[str]: List of IP addresses in the subnet
        """
        try:
            # Create an IP network object
            network = ipaddress.ip_network(subnet, strict=False)
            # Generate a list of all IP addresses in the subnet
            ip_list = [str(ip) for ip in network.hosts()]
            return ip_list
        except ValueError as e:
            raise Exception(f"Invalid subnet: {e}")
        except Exception as e:
            raise Exception(f"Error generating IP list: {e}")

    def createService(
        self, name: str, n_allocated_racks: dict[str, int], allocated_subnets: list[str], username: str
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
                    "INSERT INTO services (name, username) VALUES (%s, %s)RETURNING name, username",
                    (name, username),
                )
                # Get the newly created service data
                new_service = cursor.fetchone()

                if not new_service:
                    conn.rollback()
                    return None

                # Generate IP list from subnet
                total_ips_list = []
                available_ips_list = []
                for allocated_subnet in allocated_subnets:
                    # Check if subnet is valid
                    try:
                        ipaddress.ip_network(allocated_subnet, strict=True)
                    except ValueError:
                        raise Exception(f"Invalid subnet: {allocated_subnet}")
                    # Check if subnet already exists in the database
                    cursor.execute(
                        "SELECT * FROM subnets WHERE subnet = %s", (allocated_subnet,)
                    )
                    existing_subnet = cursor.fetchone()
                    if existing_subnet:
                        raise Exception(f"Subnet {allocated_subnet} already exists in the database")
                    ip_list = self.subnet_to_iplist(allocated_subnet)

                    # Find existing IPs in the database
                    # cursor.execute(
                    #     "SELECT * FROM IPs WHERE ip::text IN %s", (tuple(ip_list),)
                    # )
                    # existing_ips = cursor.fetchall()
                    # if existing_ips:
                    #     raise Exception(
                    #         f"IP addresses {', '.join(ip['ip'] for ip in existing_ips)} already exist in the database"
                    #     )

                    # Insert the new subnet into the subnets table
                    cursor.execute(
                        """
                        INSERT INTO subnets (subnet, service_name)
                        VALUES (%s, %s)
                        ON CONFLICT (subnet) DO NOTHING
                        RETURNING subnet
                        """,
                        (allocated_subnet, name),
                    )
                    for ip in ip_list:
                        cursor.execute(
                            """
                            INSERT INTO IPs (ip, service_name, assigned)
                            VALUES (%s, %s, FALSE)
                            """,
                            (ip, name)
                        )

                    total_ips_list += ip_list
                    available_ips_list += ip_list


                # Process allocated racks for each datacenter
                all_assigned_racks = {}
                all_hosts = []

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

                # Commit all changes
                conn.commit()

                # Create and return a Service object
                return Service(
                    name=name,
                    allocated_racks=all_assigned_racks,
                    hosts=all_hosts,
                    username=username,
                    allocated_subnets=allocated_subnets,
                    total_ip_list=total_ips_list,
                    available_ip_list=available_ips_list,
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
                # get the subnet of this service
                cursor.execute(
                    "SELECT subnet FROM subnets WHERE service_name = %s",
                    (service_name,)
                )
                subnets = cursor.fetchall()
                subnets = [subnet["subnet"] for subnet in subnets]
                # Create and return a Service object
                return Service(
                    name=data["name"],
                    allocated_racks=allocated_racks,
                    hosts=all_hosts,
                    username=data["username"],
                    allocated_subnets=subnets,
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
                    SELECT s.name, s.username, COUNT(DISTINCT r.name) AS rack_count,
                        COUNT(DISTINCT h.name) AS host_count,
                        COUNT(DISTINCT i.ip) AS ip_count
                    FROM services s
                    LEFT JOIN racks r ON s.name = r.service_name
                    LEFT JOIN hosts h ON r.name = h.rack_name
                    LEFT JOIN IPs i ON s.name = i.service_name
                    WHERE s.name IS NOT NULL
                    GROUP BY s.name, s.username
                    ORDER BY s.name
                """)
                # Fetch all services with their counts
                services_data = cursor.fetchall()
                service_list = []
                for data in services_data:
                    service_name = data["name"]

                    # get all the subnets of this service
                    cursor.execute(
                        "SELECT subnet FROM subnets WHERE service_name = %s",
                        (service_name,)
                    )
                    subnets = cursor.fetchall()
                    subnets = [subnet["subnet"] for subnet in subnets]
                    # get total IP addresses of this service
                    cursor.execute(
                        "SELECT ip FROM IPs WHERE service_name = %s",
                        (service_name,)
                    )
                    ip_data = cursor.fetchall()
                    total_ip_list = [ip["ip"] for ip in ip_data]
                    # get available IP addresses of this service
                    cursor.execute(
                        """
                        SELECT ip FROM IPs
                        WHERE service_name = %s AND assigned = FALSE
                        """,
                        (service_name,)
                    )
                    available_ip_data = cursor.fetchall()
                    available_ip_list = [ip["ip"] for ip in available_ip_data]

                    # get {dc_name: n_rack} dict
                    cursor.execute("""
                        SELECT dc_name, COUNT(DISTINCT name) AS rack_count
                        FROM racks
                        WHERE service_name = %s
                        GROUP BY dc_name
                    """, (service_name,))
                    dc_rack_rows = cursor.fetchall()
                    dc_rack_dict = {row["dc_name"]: row["rack_count"] for row in dc_rack_rows}

                    # Create a SimpleService object with summary information
                    service_list.append(
                        SimpleService(
                            name=service_name,
                            username=data["username"],
                            allocated_subnets=subnets,
                            n_allocated_racks=dc_rack_dict,
                            n_hosts=data["host_count"],
                            total_ip_list= total_ip_list,
                            available_ip_list= available_ip_list,
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
    ) -> Service | None:
        """
        Update an existing service in the database.

        Args:
            service_name (str): Name of the service to update
            new_name (str | None): New name for the service
            new_n_allocated_racks (dict[str, int] | None): New number of racks to allocate in each data center
                e.g. {"DC1": 2, "DC2": 3} means to add 2 racks in DC1 and 3 racks in DC2

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

                # Prepare update query parts for service table
                update_parts = []
                params = []

                if new_name is not None:
                    update_parts.append("name = %s")
                    params.append(new_name)

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
                    """
                    UPDATE hosts
                    SET service_name = NULL,
                        running = FALSE,
                        ip = NULL
                    WHERE service_name = %s
                    """,
                    (service_name,)
                )

                # Unassign racks from this service
                cursor.execute(
                    "UPDATE racks SET service_name = NULL WHERE service_name = %s",
                    (service_name,)
                )

                # delete subnet from this service
                cursor.execute(
                    "DELETE FROM subnets WHERE service_name = %s",
                    (service_name,)
                )

                # delete IP addresses
                cursor.execute(
                    "DELETE FROM IPs WHERE service_name = %s",
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
    def extendsubnet(
        self, service_name: str, new_subnet: str
    ) -> Service | None:
        """
        Extend the subnet of a service.
        Args:
            service_name (str): Name of the service
            new_subnet (str): New subnet in CIDR notation
        Returns:
            Service: Updated Service object
            None: If service not found or update fails
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Check if service exists
                cursor.execute(
                    "SELECT * FROM services WHERE name = %s", (service_name,)
                )
                service = cursor.fetchone()
                if not service:
                    return None

                # Generate IP list from new subnet
                try:
                    ipaddress.ip_network(new_subnet, strict=True)
                except ValueError:
                    raise Exception(f"Invalid subnet: {new_subnet}")
                # Check if subnet already exists in the database
                network = ipaddress.ip_network(new_subnet, strict=False)
                standardized_subnet = str(network.supernet(new_prefix=network.prefixlen))
                cursor.execute(
                    "SELECT * FROM subnets WHERE subnet = %s", (standardized_subnet,)
                )
                existing_subnet = cursor.fetchone()
                if existing_subnet:
                    raise Exception(f"Subnet {new_subnet} already exists in the database")
                ip_list = self.subnet_to_iplist(new_subnet)

                # Find existing IPs in the database
                # cursor.execute(
                #     "SELECT * FROM IPs WHERE ip::text = ANY(%s::text[])", (ip_list,)
                # )
                # existing_ips = cursor.fetchall()
                # if existing_ips:
                #     raise Exception(
                #         f"IP addresses {', '.join(ip['ip'] for ip in existing_ips)} already exist in the database"
                #     )

                # Insert the new subnet into the subnets table
                cursor.execute(
                    """
                    INSERT INTO subnets (subnet, service_name)
                    VALUES (%s, %s)
                    ON CONFLICT (subnet) DO NOTHING
                    RETURNING subnet
                    """,
                    (new_subnet, service_name),
                )

                for ip in ip_list:
                    cursor.execute(
                        """
                        INSERT INTO IPs (ip, service_name, assigned)
                        VALUES (%s, %s, FALSE)
                        """,
                        (ip, service_name)
                    )

                # Commit all changes
                conn.commit()

                # Return the updated service
                return self.getService(service_name)

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
                    raise Exception(
                        f"Rack {rack_name} is already assigned to a service"
                    )
                # check rack don't have any hosts assigned to it
                cursor.execute(
                    "SELECT COUNT(*) FROM hosts WHERE rack_name = %s", (rack_name,)
                )
                host_count = cursor.fetchone()[0]
                if host_count > 0:
                    # Rack has hosts assigned to it, cannot assign to service
                    raise Exception(
                        f"Rack {rack_name} has hosts assigned to it, cannot assign to service {service_name}"
                    )
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
