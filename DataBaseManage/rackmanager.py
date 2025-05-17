import os
from utils.schema import IP_range, DataCenter, Room, Rack, Host, Service, User
from utils.schema import SimpleRoom, SimpleRack, SimpleHost, SimpleService, SimpleDataCenter
from DataBaseManage.connection import BaseManager



class RackManager(BaseManager):
    
    # CREATE operations
    def createRack(self, name, height, room_id, service_id=None):
        """
        Create a new rack in a room.
        
        Args:
            name (str): Name of the rack
            height (int): Height capacity for the rack
            room_id (str): ID of the room this rack belongs to
            service_id (str, optional): ID of the service this rack is assigned to
        
        Returns:
            str: ID of the newly created rack
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                # Check if room exists and get datacenter_id
                cursor.execute("SELECT id, dc_id FROM rooms WHERE id = %s", (room_id,))
                room_info = cursor.fetchone()
                
                if room_info is None:
                    raise Exception(f"Room with ID {room_id} does not exist")
                
                datacenter_id = room_info[1]
                
                # Check if service exists (if provided)
                if service_id is not None:
                    cursor.execute("SELECT id FROM services WHERE id = %s", (service_id,))
                    if cursor.fetchone() is None:
                        raise Exception(f"Service with ID {service_id} does not exist")
                
                # Generate a new UUID for the rack
                cursor.execute("SELECT gen_random_uuid()")
                rack_id = cursor.fetchone()[0]
                
                # Insert the new rack
                cursor.execute(
                    "INSERT INTO racks (id, name, height, n_hosts, service_id, dc_id, room_id) VALUES (%s, %s, %s, 0, %s, %s, %s)",
                    (rack_id, name, height, service_id, datacenter_id, room_id)
                )
                
                # Update the rack count in the room
                cursor.execute(
                    "UPDATE rooms SET n_racks = n_racks + 1 WHERE id = %s",
                    (room_id,)
                )
                
                # Update the rack count in the datacenter
                cursor.execute(
                    "UPDATE datacenters SET n_racks = n_racks + 1 WHERE id = %s",
                    (datacenter_id,)
                )
                
                # Update the rack count in the service (if provided)
                if service_id is not None:
                    cursor.execute(
                        "UPDATE services SET n_racks = n_racks + 1 WHERE id = %s",
                        (service_id,)
                    )
                
                conn.commit()
                return rack_id
                
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)
    
    # READ operations
    def getRack(self, rack_id):
        """
        Get a rack by ID.
        
        Args:
            rack_id (str): ID of the rack to retrieve
        
        Returns:
            Rack: Rack object if found, None otherwise
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, name, height, n_hosts, service_id, dc_id, room_id FROM racks WHERE id = %s",
                    (rack_id,)
                )
                result = cursor.fetchone()
                
                if result is None:
                    return None
                
                # Get hosts for this rack
                cursor.execute(
                    "SELECT id, name, height, ip, service_id, rack_id, pos FROM hosts WHERE id = %s",
                    (rack_id,)
                )
                hosts_data = cursor.fetchall()
                
                # Convert to SimpleHost objects
                hosts = []
                for host_data in hosts_data:
                    hosts.append(
                        SimpleHost(
                            id=host_data['id'],
                            name=host_data['name'],
                            height=host_data['height'],
                            status="active",  # Default status
                            rack_id=host_data['rack_id'],
                            pos=host_data['pos']
                        )
                    )
                
                # Create and return the Rack object
                return Rack(
                    id=result[0],
                    name=result[1],
                    height=result[2],
                    hosts=hosts,
                    n_hosts=result[3],
                    service_id=result[4],
                    dc_id=result[5],
                    room_id=result[6]
                )
                
        except Exception as e:
            raise e
        finally:
            if conn:
                self.release_connection(conn)
        

        
    # UPDATE operations
    def updateRack(self, rack_id, room_id, name=None, height=None, service_id=None):
        """
        Update a rack's information.
        
        Args:
            rack_id (str): ID of the rack to update
            room_id (str): ID of the room this rack belongs to
            name (str, optional): New name for the rack
            height (int, optional): New height for the rack
            service_id (str, optional): New service ID for the rack
        
        Returns:
            bool: True if rack was successfully updated, False if not found
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                # First check if rack exists and get its current service_id
                cursor.execute("SELECT id, service_id FROM racks WHERE id = %s", (rack_id,))
                rack_info = cursor.fetchone()
                
                if rack_info is None:
                    return False
                
                current_service_id = rack_info[1]
                
                # Check if service exists (if a new one is provided)
                if service_id is not None and service_id != current_service_id:
                    cursor.execute("SELECT id FROM services WHERE id = %s", (service_id,))
                    if cursor.fetchone() is None:
                        raise Exception(f"Service with ID {service_id} does not exist")
                
                # Build the update query based on provided parameters
                update_params = []
                query_parts = []
                query_parts.append("room_id = %s")
                if name is not None:
                    query_parts.append("name = %s")
                    update_params.append(name)
                
                if height is not None:
                    query_parts.append("height = %s")
                    update_params.append(height)
                
                if service_id is not None:
                    query_parts.append("service_id = %s")
                    update_params.append(service_id)
                
                if not query_parts:
                    # Nothing to update
                    return True
                
                query = f"UPDATE racks SET {', '.join(query_parts)} WHERE id = %s"
                update_params.append(rack_id)
                
                cursor.execute(query, tuple(update_params))
                
                # Update service counts if service_id has changed
                if service_id is not None and service_id != current_service_id:
                    # Decrement rack count in old service if it exists
                    if current_service_id is not None:
                        cursor.execute(
                            "UPDATE services SET n_racks = n_racks - 1 WHERE id = %s",
                            (current_service_id,)
                        )
                    
                    # Increment rack count in new service
                    cursor.execute(
                        "UPDATE services SET n_racks = n_racks + 1 WHERE id = %s",
                        (service_id,)
                    )
                # Update the room count in the room
                cursor.execute(
                    "UPDATE rooms SET n_racks = n_racks + 1 WHERE id = %s",
                    (room_id,)
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
    def deleteRack(self, rack_id):
        """
        Delete a rack from the database.
        
        Args:
            rack_id (str): ID of the rack to delete
        
        Returns:
            bool: True if rack was successfully deleted, False if not found
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                # First check if rack exists and get its room_id, datacenter_id, and service_id
                cursor.execute("SELECT id, room_id, dc_id, service_id FROM racks WHERE id = %s", (rack_id,))
                rack_info = cursor.fetchone()
                
                if rack_info is None:
                    return False
                
                room_id = rack_info[1]
                datacenter_id = rack_info[2]
                service_id = rack_info[3]
                
                # Check if rack has any hosts (optional: prevent deletion if it has dependencies)
                cursor.execute("SELECT COUNT(*) FROM hosts WHERE rack_id = %s", (rack_id,))
                host_count = cursor.fetchone()[0]
                
                if host_count > 0:
                    # You may want to raise a custom exception here instead
                    # to indicate that the rack has dependencies
                    raise Exception(f"Cannot delete rack with ID {rack_id} because it contains {host_count} hosts")
                
                # Delete the rack
                cursor.execute("DELETE FROM racks WHERE id = %s", (rack_id,))
                
                # Update the rack count in the room
                cursor.execute(
                    "UPDATE rooms SET n_racks = n_racks - 1 WHERE id = %s",
                    (room_id,)
                )
                
                # Update the rack count in the datacenter
                cursor.execute(
                    "UPDATE datacenters SET n_racks = n_racks - 1 WHERE id = %s",
                    (datacenter_id,)
                )
                
                # Update the rack count in the service (if assigned to a service)
                if service_id is not None:
                    cursor.execute(
                        "UPDATE services SET n_racks = n_racks - 1 WHERE id = %s",
                        (service_id,)
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

