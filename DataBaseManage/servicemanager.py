from utils.schema import Service, SimpleRack, SimpleService
from DataBaseManage.connection import BaseManager
import psycopg2
import psycopg2.extras


class ServiceManager(BaseManager):
    """Class for managing service operations"""

    # Service operations
    def createService(
        self, name: str, dc_id: str, n_racks: int, total_ip: int
    ) -> Service | None:
        """
        Create a new service in the database.

        Args:
            name (str): Name of the service
            dc_id (str): Data center that the service belongs to
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
                    "SELECT id, name FROM datacenters WHERE id = %s", (dc_id,)
                )
                dc_data = cursor.fetchone()
                if dc_data is None:
                    raise Exception(f"Datacenter with ID {dc_id} does not exist")

                # Insert the new service
                cursor.execute(
                    """
                    INSERT INTO services (name, n_racks, n_hosts, total_ip, dc_id, dc_name)
                    VALUES (%s, %s, 0, %s, %s, %s)
                    RETURNING id, name
                    """,
                    (name, n_racks, total_ip, dc_data["id"], dc_data["name"]),
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
                    SELECT id FROM racks 
                    WHERE service_id IS NULL
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
                    rack_id = rack_data["id"]

                    cursor.execute(
                        """
                        UPDATE racks 
                        SET service_id = %s 
                        WHERE id = %s
                        RETURNING *
                        """,
                        (service_id, rack_id),
                    )
                    updated_rack = cursor.fetchone()
                    if updated_rack:
                        assigned_racks.append(
                            SimpleRack(
                                id=updated_rack["id"],
                                name=updated_rack["name"],
                                height=updated_rack["height"],
                                capacity=updated_rack["capacity"],
                                n_hosts=updated_rack["n_hosts"],
                                service_id=updated_rack["service_id"],
                                service_name=new_service["name"],
                                room_id=updated_rack["room_id"],
                            )
                        )

                # Get {total_ip} IP addresses in the datacenter
                cursor.execute(
                    """
                    SELECT ip FROM service_ips WHERE dc_id = %s AND service_id = NULL LIMIT %s
                    """,
                    (dc_data["id"], total_ip),
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
                        UPDATE service_ips 
                        SET service_id = %s 
                        WHERE ip = %s
                        """,
                        (service_id, ip),
                    )

                # Commit all changes
                conn.commit()

                # Create and return a Service object
                return Service(
                    id=service_id,
                    name=name,
                    n_racks=n_racks,
                    racks=assigned_racks,
                    n_hosts=0,
                    total_ip=total_ip,
                    total_ip_list=total_ip_list,
                    available_ip=total_ip,
                    available_ip_list=total_ip_list,
                    dc_id=dc_data["id"],
                    dc_name=dc_data["name"],
                )

        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    def getService(self, service_id=None) -> Service | list[SimpleService] | None:
        """
        Get services information.
        If service_id is provided, returns specific service as Service object,
        otherwise returns list of Service objects.
        Returns None if service_id is provided but not found.
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                if service_id:
                    # Get the specific service
                    cursor.execute(
                        "SELECT * FROM services WHERE id = %s", (service_id,)
                    )
                    data = cursor.fetchone()
                    if not data:
                        return None

                    # Get racks for this service
                    cursor.execute(
                        "SELECT * FROM racks WHERE service_id = %s", (service_id,)
                    )
                    racks_data = cursor.fetchall()

                    # Convert to SimpleRack objects
                    racks = [
                        SimpleRack(
                            id=rack_data["id"],
                            name=rack_data["name"],
                            height=rack_data["height"],
                            capacity=rack_data["capacity"],
                            n_hosts=rack_data["n_hosts"],
                            service_id=rack_data["service_id"],
                            service_name=data["name"],
                            room_id=rack_data["room_id"],
                        )
                        for rack_data in racks_data
                    ]

                    # Get IP addresses for this service
                    cursor.execute(
                        "SELECT ip, assigned FROM service_ips WHERE service_id = %s",
                        (service_id,),
                    )
                    ip_data = cursor.fetchall()

                    total_ip_list = [ip["ip"] for ip in ip_data]
                    available_ip_list = [
                        ip["ip"] for ip in ip_data if ip["assigned"] is False
                    ]

                    # Create and return a Service object
                    return Service(
                        id=data["id"],
                        name=data["name"],
                        n_racks=data["n_racks"],
                        racks=racks,
                        n_hosts=data["n_hosts"],
                        total_ip=len(total_ip_list),
                        total_ip_list=total_ip_list,
                        available_ip=len(available_ip_list),
                        available_ip_list=available_ip_list,
                        dc_id=data["dc_id"],
                        dc_name=data["dc_name"],
                    )
                else:
                    # Get all services
                    cursor.execute("SELECT * FROM services ORDER BY name")
                    services_data = cursor.fetchall()

                    # Create a list to store Service objects
                    services = []

                    # Get racks for each service
                    for data in services_data:
                        cursor.execute(
                            "SELECT * FROM racks WHERE service_id = %s", (data["id"],)
                        )
                        racks_data = cursor.fetchall()

                        # Convert to SimpleRack objects
                        racks = []
                        for rack_data in racks_data:
                            rack = SimpleRack(
                                id=rack_data["id"],
                            )
                            racks.append(rack)

                        # Get IP addresses for this service
                        cursor.execute(
                            "SELECT ip FROM service_ips WHERE service_id = %s",
                            (srv_id,),
                        )
                        ip_data = cursor.fetchall()
                        ip_list = [ip["ip"] for ip in ip_data]

                        # Create Service object and append to list
                        services.append(
                            Service(
                                id=data["id"],
                                name=data["name"],
                                racks=racks,
                                n_racks=data["n_racks"],
                                n_hosts=data["n_hosts"],
                                total_ip=data["total_ip"],
                                ip_list=ip_list,
                            )
                        )

                    return services
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    def updateService(self, service_id, name=None, racks=None, ip_list=None):
        """
        Update an existing service in the database.

        Args:
            service_id (str): ID of the service to update
            name (str, optional): New name for the service
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
                cursor.execute("SELECT * FROM services WHERE id = %s", (service_id,))
                service = cursor.fetchone()
                if not service:
                    return None

                # Prepare update query parts
                update_parts = []
                params = []

                if name is not None:
                    update_parts.append("name = %s")
                    params.append(name)

                # Handle racks if provided
                if racks is not None:
                    # First, unassign all racks from this service
                    cursor.execute(
                        "UPDATE racks SET service_id = NULL WHERE service_id = %s",
                        (service_id,),
                    )

                    # Then assign provided racks to this service
                    n_racks = len(racks)
                    update_parts.append("n_racks = %s")
                    params.append(n_racks)

                    for rack in racks:
                        cursor.execute(
                            "UPDATE racks SET service_id = %s WHERE id = %s",
                            (service_id, rack.id),
                        )

                # Handle IP addresses if provided
                if ip_list is not None:
                    # First, delete all existing IP addresses for this service
                    cursor.execute(
                        "DELETE FROM service_ips WHERE service_id = %s", (service_id,)
                    )

                    # Then add new IP addresses
                    total_ip = len(ip_list)
                    update_parts.append("total_ip = %s")
                    params.append(total_ip)

                    for ip in ip_list:
                        cursor.execute(
                            "INSERT INTO service_ips (service_id, ip) VALUES (%s, %s)",
                            (service_id, ip),
                        )

                # Update the service if there are changes
                if update_parts:
                    # Add updated_at to be updated
                    update_parts.append("updated_at = CURRENT_TIMESTAMP")

                    # Build and execute update query
                    query = f"UPDATE services SET {', '.join(update_parts)} WHERE id = %s RETURNING *"
                    params.append(service_id)

                    cursor.execute(query, params)
                    updated_service = cursor.fetchone()
                else:
                    updated_service = service

                # Get updated racks for this service
                cursor.execute(
                    "SELECT * FROM racks WHERE service_id = %s", (service_id,)
                )
                racks_data = cursor.fetchall()

                # Convert to SimpleRack objects
                updated_racks = []
                for rack_data in racks_data:
                    rack = SimpleRack(
                        id=rack_data["id"],
                        name=rack_data["name"],
                        room_id=rack_data["room_id"],
                        service_id=rack_data["service_id"],
                    )
                    updated_racks.append(rack)

                # Get updated IP addresses for this service
                cursor.execute(
                    "SELECT ip FROM service_ips WHERE service_id = %s", (service_id,)
                )
                ip_data = cursor.fetchall()
                updated_ip_list = [ip["ip"] for ip in ip_data]

                # Commit all changes
                conn.commit()

                # Create and return updated Service object
                return Service(
                    id=updated_service["id"],
                    name=updated_service["name"],
                    racks=updated_racks,
                    n_racks=len(updated_racks),
                    n_hosts=updated_service["n_hosts"],
                    total_ip=len(updated_ip_list),
                    ip_list=updated_ip_list,
                )

        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    def deleteService(self, service_id):
        """
        Delete a service from the database.

        Args:
            service_id (str): ID of the service to delete

        Returns:
            bool: True if service was successfully deleted, False if not found
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                # First check if service exists
                cursor.execute("SELECT id FROM services WHERE id = %s", (service_id,))
                if cursor.fetchone() is None:
                    return False

                # Unassign racks from this service (set service_id to NULL)
                cursor.execute(
                    "UPDATE racks SET service_id = NULL WHERE service_id = %s",
                    (service_id,),
                )

                # Delete IP addresses for this service
                cursor.execute(
                    "DELETE FROM service_ips WHERE service_id = %s", (service_id,)
                )

                # Delete the service
                cursor.execute("DELETE FROM services WHERE id = %s", (service_id,))

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

    def assignRackToService(self, service_id, rack_id):
        """
        Assign a rack to a service.

        Args:
            service_id (str): ID of the service
            rack_id (str): ID of the rack to assign

        Returns:
            bool: True if assignment was successful, False otherwise
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                # Check if service exists
                cursor.execute("SELECT id FROM services WHERE id = %s", (service_id,))
                if cursor.fetchone() is None:
                    return False

                # Check if rack exists
                cursor.execute("SELECT id FROM racks WHERE id = %s", (rack_id,))
                if cursor.fetchone() is None:
                    return False

                # Assign rack to service
                cursor.execute(
                    "UPDATE racks SET service_id = %s WHERE id = %s",
                    (service_id, rack_id),
                )

                if cursor.rowcount <= 0:
                    return False

                # Update service rack count
                cursor.execute(
                    """
                    UPDATE services 
                    SET n_racks = (SELECT COUNT(*) FROM racks WHERE service_id = %s)
                    WHERE id = %s
                    """,
                    (service_id, service_id),
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

    def unassignRackFromService(self, rack_id):
        """
        Unassign a rack from any service.

        Args:
            rack_id (str): ID of the rack to unassign

        Returns:
            bool: True if unassignment was successful, False otherwise
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                # Get the current service_id before unassigning
                cursor.execute("SELECT service_id FROM racks WHERE id = %s", (rack_id,))
                result = cursor.fetchone()
                if result is None:
                    return False

                service_id = result[0]
                if service_id is None:
                    # Rack is not assigned to any service
                    return True

                # Unassign rack
                cursor.execute(
                    "UPDATE racks SET service_id = NULL WHERE id = %s", (rack_id,)
                )

                if cursor.rowcount <= 0:
                    return False

                # Update service rack count
                cursor.execute(
                    """
                    UPDATE services 
                    SET n_racks = (SELECT COUNT(*) FROM racks WHERE service_id = %s)
                    WHERE id = %s
                    """,
                    (service_id, service_id),
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

    def addIPToService(self, service_id, ip_address):
        """
        Add an IP address to a service.

        Args:
            service_id (str): ID of the service
            ip_address (str): IP address to add

        Returns:
            bool: True if addition was successful, False otherwise
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                # Check if service exists
                cursor.execute("SELECT id FROM services WHERE id = %s", (service_id,))
                if cursor.fetchone() is None:
                    return False

                # Add IP address
                cursor.execute(
                    "INSERT INTO service_ips (service_id, ip) VALUES (%s, %s)",
                    (service_id, ip_address),
                )

                # Update service IP count
                cursor.execute(
                    """
                    UPDATE services 
                    SET total_ip = (SELECT COUNT(*) FROM service_ips WHERE service_id = %s)
                    WHERE id = %s
                    """,
                    (service_id, service_id),
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

    def removeIPFromService(self, service_id, ip_address):
        """
        Remove an IP address from a service.

        Args:
            service_id (str): ID of the service
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
                    "DELETE FROM service_ips WHERE service_id = %s AND ip = %s",
                    (service_id, ip_address),
                )

                if cursor.rowcount <= 0:
                    return False

                # Update service IP count
                cursor.execute(
                    """
                    UPDATE services 
                    SET total_ip = (SELECT COUNT(*) FROM service_ips WHERE service_id = %s)
                    WHERE id = %s
                    """,
                    (service_id, service_id),
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

    def updateHostCount(self, service_id):
        """
        Update the host count for a service based on assigned racks.

        Args:
            service_id (str): ID of the service

        Returns:
            int: Updated host count, -1 if service not found
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                # Check if service exists
                cursor.execute("SELECT id FROM services WHERE id = %s", (service_id,))
                if cursor.fetchone() is None:
                    return -1

                # Calculate host count from assigned racks
                cursor.execute(
                    """
                    SELECT COALESCE(SUM(n_hosts), 0) as total_hosts 
                    FROM racks 
                    WHERE service_id = %s
                    """,
                    (service_id,),
                )

                total_hosts = cursor.fetchone()[0]

                # Update service host count
                cursor.execute(
                    "UPDATE services SET n_hosts = %s WHERE id = %s",
                    (total_hosts, service_id),
                )

                # Commit changes
                conn.commit()

                return total_hosts

        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)
