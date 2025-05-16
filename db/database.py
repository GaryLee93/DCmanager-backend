"""
Datacenter Management System - Backend
A Python API for managing datacenter resources using the PostgreSQL database schema provided.
"""

import os
import psycopg2
import psycopg2.extras
from psycopg2.pool import SimpleConnectionPool
from datetime import datetime
import uuid
from utils.schema import IP_range, DataCenter, Room, Rack, Host, Service, User
from utils.schema import SimpleRoom, SimpleRack, SimpleHost, SimpleService, SimpleDataCenter
# Database connection configuration
DB_CONFIG = {
    'dbname': os.environ.get('DB_NAME', 'datacenter_management'),
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', 'postgres'),
    'host': os.environ.get('DB_HOST', 'db'),
    'port': os.environ.get('DB_PORT', '5432')
}

def test_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print(f"Connected to database! PostgreSQL version: {version[0]}")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Database connection failed: {e}")


# Create a connection pool
pool = SimpleConnectionPool(1, 10, **DB_CONFIG)

# new schema
class IPRangeManager:
    """Class for managing IP ranges operations"""
    
    @staticmethod
    def get_connection():
        """Get a connection from the pool"""
        return pool.getconn()
    
    @staticmethod
    def release_connection(conn):
        """Release a connection back to the pool"""
        pool.putconn(conn)
    
    def get_ip_ranges(self, datacenter_id=None):
        """
        Get IP ranges for a datacenter.
        If datacenter_id is provided, returns IP ranges for that specific datacenter,
        otherwise returns all IP ranges.
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                if datacenter_id:
                    cursor.execute("SELECT * FROM ip_ranges WHERE datacenter_id = %s", (datacenter_id,))
                else:
                    cursor.execute("SELECT * FROM ip_ranges")
                
                ip_ranges_data = cursor.fetchall()
                
                # Convert to IP_range objects
                ip_ranges = []
                for data in ip_ranges_data:
                    ip_range = IP_range(
                        start_IP=data['start_ip'],
                        end_IP=data['end_ip']
                    )
                    ip_ranges.append(ip_range)
                
                return ip_ranges
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)
    
    def add_ip_range(self, datacenter_id, start_ip, end_ip):
        """
        Add a new IP range to a datacenter.
        
        Args:
            datacenter_id (str): ID of the datacenter
            start_ip (str): Start IP address
            end_ip (str): End IP address
            
        Returns:
            IP_range: The newly created IP range object
        """
        # Validate IP addresses
        try:
            import ipaddress
            start = ipaddress.ip_address(start_ip)
            end = ipaddress.ip_address(end_ip)
            if start > end:
                raise ValueError("Start IP must be less than or equal to End IP")
        except ValueError as e:
            raise ValueError(f"Invalid IP address format: {e}")
            
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Check if datacenter exists
                cursor.execute("SELECT id FROM datacenters WHERE id = %s", (datacenter_id,))
                if cursor.fetchone() is None:
                    raise ValueError(f"Datacenter with ID {datacenter_id} not found")
                
                # Insert the new IP range
                cursor.execute(
                    """
                    INSERT INTO ip_ranges (datacenter_id, start_ip, end_ip)
                    VALUES (%s, %s, %s)
                    RETURNING id, datacenter_id, start_ip, end_ip
                    """,
                    (datacenter_id, start_ip, end_ip)
                )
                
                conn.commit()
                new_ip_range = cursor.fetchone()
                
                return IP_range(
                    start_IP=new_ip_range['start_ip'],
                    end_IP=new_ip_range['end_ip']
                )
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)
    
    def delete_ip_range(self, ip_range_id):
        """
        Delete an IP range.
        
        Args:
            ip_range_id (str): ID of the IP range to delete
            
        Returns:
            bool: True if deleted successfully, False if not found
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM ip_ranges WHERE id = %s", (ip_range_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)


class DatacenterManager:
    """Class for managing datacenter operations"""

    @staticmethod
    def get_connection():
        """Get a connection from the pool"""
        return pool.getconn()

    @staticmethod
    def release_connection(conn):
        """Release a connection back to the pool"""
        pool.putconn(conn)

    # Datacenter operations
    def getDatacenter(self, datacenter_id):
        """
        Get datacenters information.
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Get the specific datacenter
                cursor.execute("SELECT * FROM datacenters WHERE id = %s", (datacenter_id,))
                data = cursor.fetchone()
                if not data:
                    return None
                
                # Get rooms for this datacenter
                cursor.execute("SELECT * FROM rooms WHERE id = %s", (datacenter_id,))
                rooms_data = cursor.fetchall()
                
                # Convert to SimpleRoom objects
                rooms = []
                for room_data in rooms_data:
                    room = SimpleRoom(
                        id=room_data['id'],
                        name=room_data['name'],
                        datacenter_id=room_data['datacenter_id']
                    )
                    rooms.append(room)
                
                # Get IP ranges for this datacenter
                ip_range_manager = IPRangeManager()
                ip_ranges = ip_range_manager.get_ip_ranges(datacenter_id)
                
                # Create and return a DataCenter object
                return DataCenter(
                    id=data['id'],
                    name=data['name'],
                    height=data['height'],
                    rooms=rooms,
                    n_rooms=data['n_rooms'],
                    n_racks=data['n_racks'],
                    n_hosts=data['n_hosts'],
                    ip_ranges=ip_ranges
                )
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
            with conn.cursor() as cursor:
                # First check if datacenter exists
                cursor.execute("SELECT id FROM datacenters WHERE id = %s", (datacenter_id,))
                if cursor.fetchone() is None:
                    return False
                
                # Check if datacenter has any rooms
                cursor.execute("SELECT COUNT(*) FROM rooms WHERE id = %s", (datacenter_id,))
                room_count = cursor.fetchone()[0]
                
                if room_count > 0:
                    raise Exception(f"Cannot delete datacenter with ID {datacenter_id} because it contains {room_count} rooms")
                
                # Delete associated IP ranges first
                cursor.execute("DELETE FROM ip_ranges WHERE id = %s", (datacenter_id,))
                
                # Delete the datacenter
                cursor.execute("DELETE FROM datacenters WHERE id = %s", (datacenter_id,))
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
                
    def updateDatacenter(self, datacenter_id, name=None, default_height=None, ip_ranges=None):
        """
        Update an existing datacenter in the database.
        
        Args:
            datacenter_id (str): ID of the datacenter to update
            name (str, optional): New name for the datacenter
            default_height (int, optional): New default rack height for the datacenter
            ip_ranges (list[IP_range], optional): New IP ranges for the datacenter
        
        Returns:
            DataCenter: Updated DataCenter object
            None: If datacenter not found or update fails
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # First check if datacenter exists
                cursor.execute("SELECT * FROM datacenters WHERE id = %s", (datacenter_id,))
                datacenter = cursor.fetchone()
                if not datacenter:
                    return None
                
                # Prepare update query parts
                update_parts = []
                params = []
                
                if name is not None:
                    update_parts.append("name = %s")
                    params.append(name)
                    
                if default_height is not None:
                    update_parts.append("height = %s")
                    params.append(default_height)
                
                # If no database updates requested but ip_ranges provided, 
                # we'll still need to process IP ranges
                if update_parts:
                    # Add updated_at to be updated
                    update_parts.append("updated_at = CURRENT_TIMESTAMP")
                    
                    # Build and execute update query
                    query = f"UPDATE datacenters SET {', '.join(update_parts)} WHERE id = %s RETURNING *"
                    params.append(datacenter_id)
                    
                    cursor.execute(query, params)
                    conn.commit()
                    
                    updated_datacenter = cursor.fetchone()
                else:
                    updated_datacenter = datacenter
                
                # Get rooms for this datacenter
                cursor.execute("SELECT * FROM rooms WHERE id = %s", (datacenter_id,))
                rooms_data = cursor.fetchall()
                
                # Convert to SimpleRoom objects
                rooms = []
                for room_data in rooms_data:
                    room = SimpleRoom(
                        id=room_data['id'],
                        name=room_data['name'],
                        datacenter_id=room_data['datacenter_id']
                    )
                    rooms.append(room)
                
                # Handle IP ranges if provided
                ip_range_manager = IPRangeManager()
                if ip_ranges is not None:
                    # Delete existing IP ranges for this datacenter
                    cursor.execute("DELETE FROM ip_ranges WHERE id = %s", (datacenter_id,))
                    conn.commit()
                    
                    # Add new IP ranges
                    ip_range_objects = []
                    for ip_range in ip_ranges:
                        added_range = ip_range_manager.add_ip_range(
                            datacenter_id, 
                            ip_range.start_IP, 
                            ip_range.end_IP
                        )
                        ip_range_objects.append(added_range)
                else:
                    # Get existing IP ranges
                    ip_range_objects = ip_range_manager.get_ip_ranges(datacenter_id)
                
                # Create and return updated DataCenter object
                return DataCenter(
                    id=updated_datacenter['id'],
                    name=updated_datacenter['name'],
                    height=updated_datacenter['height'],
                    rooms=rooms,
                    n_rooms=updated_datacenter['n_rooms'],
                    n_racks=updated_datacenter['n_racks'],
                    n_hosts=updated_datacenter['n_hosts'],
                    ip_ranges=ip_range_objects
                )
                
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)
                
    def createDatacenter(self, name, default_height=42, ip_ranges=None):
        """
        Create a new datacenter in the database.
        
        Args:
            name (str): Name of the datacenter
            default_height (int, optional): Default rack height for the datacenter. Defaults to 42.
            ip_ranges (list[IP_range], optional): IP ranges for the datacenter. Defaults to None.
        
        Returns:
            DataCenter: A DataCenter object representing the newly created datacenter.
            None: If creation fails
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Insert the new datacenter
                cursor.execute(
                    """
                    INSERT INTO datacenters (name, height, n_rooms, n_racks, n_hosts)
                    VALUES (%s, %s, 0, 0, 0)
                    RETURNING id, name, height, n_rooms, n_racks, n_hosts
                    """,
                    (name, default_height)
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
                            new_datacenter['id'], 
                            ip_range.start_IP, 
                            ip_range.end_IP
                        )
                        ip_range_objects.append(added_range)
                
                # Create and return a DataCenter object
                return DataCenter(
                    id=new_datacenter['id'],
                    name=new_datacenter['name'],
                    height=new_datacenter['height'],
                    rooms=[],  # New datacenter has no rooms yet
                    n_rooms=new_datacenter['n_rooms'],
                    n_racks=new_datacenter['n_racks'],
                    n_hosts=new_datacenter['n_hosts'],
                    ip_ranges=ip_range_objects
                )
                
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    def getAllDatacenters(self):
        """
        Get all datacenters.
        
        Returns:
            list: List of DataCenter objects
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM datacenters ORDER BY name")
                datacenters_data = cursor.fetchall()
                
                # Create a list to store DataCenter objects
                datacenters = []
                
                # Process each datacenter
                for data in datacenters_data:
                    dc_id = data['id']
                    # Get rooms for this datacenter
                    cursor.execute("SELECT * FROM rooms WHERE id = %s", (dc_id,))                    
                    
                    # Create DataCenter object and append to list
                    datacenters.append(
                        SimpleDataCenter(
                            id=data['id'],
                            name=data['name'],
                            height=data['height'],
                            n_rooms=data['n_rooms'],
                            n_racks=data['n_racks'],
                            n_hosts=data['n_hosts'],
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


class RoomManager:

    @staticmethod
    def get_connection():
        """Get a connection from the pool"""
        return pool.getconn()

    @staticmethod
    def release_connection(conn):
        """Release a connection back to the pool"""
        pool.putconn(conn)
    
    # CREATE operations
    def createRoom(self, name, height, datacenter_id):
        """
        Create a new room in a datacenter.
        
        Args:
            name (str): Name of the room
            height (int): Height capacity for the room
            datacenter_id (str): ID of the datacenter this room belongs to
        
        Returns:
            str: ID of the newly created room
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                # Check if datacenter exists
                cursor.execute("SELECT id FROM datacenters WHERE id = %s", (datacenter_id,))
                if cursor.fetchone() is None:
                    raise Exception(f"Datacenter with ID {datacenter_id} does not exist")
                
                # Generate a new UUID for the room
                cursor.execute("SELECT gen_random_uuid()")
                room_id = cursor.fetchone()[0]
                
                # Insert the new room
                cursor.execute(
                    "INSERT INTO rooms (id, name, height, n_racks, n_hosts, datacenter_id) VALUES (%s, %s, %s, 0, 0, %s)",
                    (room_id, name, height, datacenter_id)
                )
                
                # Update the room count in the datacenter
                cursor.execute(
                    "UPDATE datacenters SET n_rooms = n_rooms + 1 WHERE id = %s",
                    (datacenter_id,)
                )
                
                conn.commit()
                return room_id
                
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)
    
    # READ operations
    def getRoom(self, room_id):
        """
        Get a room by ID.
        
        Args:
            room_id (str): ID of the room to retrieve
        
        Returns:
            Room: Room object if found, None otherwise
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, name, height, n_racks, n_hosts, datacenter_id FROM rooms WHERE id = %s",
                    (room_id,)
                )
                result = cursor.fetchone()
                
                if result is None:
                    return None
                # Get full rack information for this room
                cursor.execute(
                    "SELECT id, name, height FROM racks WHERE id = %s",
                    (room_id,)
                )
                racks_data = cursor.fetchall()
                
                # Create SimpleRack objects
                racks = []
                for rack_data in racks_data:
                    racks.append(
                        SimpleRack(
                            id=rack_data['id'],
                            name=rack_data['name'],
                            height=rack_data['height'],
                            room_id=room_id
                        )
                    )
                
                # Create and return the Room object
                return Room(
                    id=result['id'],
                    name=result['name'],
                    height=result['height'],
                    racks=racks,  # Now using SimpleRack objects
                    n_racks=result['n_racks'],
                    n_hosts=result['n_hosts'],
                    dc_id=result['datacenter_id']
                )
                                
        except Exception as e:
            raise e
        finally:
            if conn:
                self.release_connection(conn)
    
    
    # UPDATE operations
    def updateRoom(self, room_id, name=None, height=None):
        """
        Update a room's information.
        
        Args:
            room_id (str): ID of the room to update
            name (str, optional): New name for the room
            height (int, optional): New height for the room
        
        Returns:
            bool: True if room was successfully updated, False if not found
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                # First check if room exists
                cursor.execute("SELECT id FROM rooms WHERE id = %s", (room_id,))
                if cursor.fetchone() is None:
                    return False
                
                # Build the update query based on provided parameters
                update_params = []
                query_parts = []
                
                if name is not None:
                    query_parts.append("name = %s")
                    update_params.append(name)
                
                if height is not None:
                    query_parts.append("height = %s")
                    update_params.append(height)
                
                if not query_parts:
                    # Nothing to update
                    return True
                
                query = f"UPDATE rooms SET {', '.join(query_parts)} WHERE id = %s"
                update_params.append(room_id)
                
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
    def deleteRoom(self, room_id):
        """
        Delete a room from the database.
        
        Args:
            room_id (str): ID of the room to delete
        
        Returns:
            bool: True if room was successfully deleted, False if not found
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                # First check if room exists and get its datacenter_id
                cursor.execute("SELECT id, datacenter_id FROM rooms WHERE id = %s", (room_id,))
                room_info = cursor.fetchone()
                
                if room_info is None:
                    return False
                
                datacenter_id = room_info[1]
                
                # Check if room has any racks (optional: prevent deletion if it has dependencies)
                cursor.execute("SELECT COUNT(*) FROM racks WHERE id = %s", (room_id,))
                rack_count = cursor.fetchone()[0]
                
                if rack_count > 0:
                    # You may want to raise a custom exception here instead to indicate that the room has dependencies
                    raise Exception(f"Cannot delete room with ID {room_id} because it contains {rack_count} racks")
                
                # Delete the room
                cursor.execute("DELETE FROM rooms WHERE id = %s", (room_id,))
                
                # Update the room count in the datacenter
                cursor.execute(
                    "UPDATE datacenters SET n_rooms = n_rooms - 1 WHERE id = %s",
                    (datacenter_id,)
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
    

class RackManager:

    @staticmethod
    def get_connection():
        """Get a connection from the pool"""
        return pool.getconn()

    @staticmethod
    def release_connection(conn):
        """Release a connection back to the pool"""
        pool.putconn(conn)    
    
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

class HostManager:

    @staticmethod
    def get_connection():
        """Get a connection from the pool"""
        return pool.getconn()

    @staticmethod
    def release_connection(conn):
        """Release a connection back to the pool"""
        pool.putconn(conn)    
    # CREATE operations
    def createHost(self, name, height, ip, rack_id, service_id=None):
        """
        Create a new host in a rack.
        
        Args:
            name (str): Name of the host
            height (int): Height of the host in rack units
            ip (str): IP address of the host
            rack_id (str): ID of the rack this host belongs to
            service_id (str, optional): ID of the service this host is assigned to
        
        Returns:
            str: ID of the newly created host
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                # Check if rack exists and get its room_id and datacenter_id
                cursor.execute("SELECT id, room_id, dc_id FROM racks WHERE id = %s", (rack_id,))
                rack_info = cursor.fetchone()
                
                if rack_info is None:
                    raise Exception(f"Rack with ID {rack_id} does not exist")
                
                room_id = rack_info[1]
                datacenter_id = rack_info[2]
                
                # Check if service exists (if provided)
                if service_id is not None:
                    cursor.execute("SELECT id FROM services WHERE id = %s", (service_id,))
                    if cursor.fetchone() is None:
                        raise Exception(f"Service with ID {service_id} does not exist")
                
                # Check if IP address is unique
                cursor.execute("SELECT id FROM hosts WHERE ip = %s", (ip,))
                if cursor.fetchone() is not None:
                    raise Exception(f"Host with IP {ip} already exists")
                
                # Generate a new UUID for the host
                cursor.execute("SELECT gen_random_uuid()")
                host_id = cursor.fetchone()[0]
                
                # Insert the new host
                cursor.execute(
                    "INSERT INTO hosts (id, name, height, ip, service_id, dc_id, room_id, rack_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (host_id, name, height, ip, service_id, datacenter_id, room_id, rack_id)
                )
                
                # Update the host count in the rack
                cursor.execute(
                    "UPDATE racks SET n_hosts = n_hosts + 1 WHERE id = %s",
                    (rack_id,)
                )
                
                # Update the host count in the room
                cursor.execute(
                    "UPDATE rooms SET n_hosts = n_hosts + 1 WHERE id = %s",
                    (room_id,)
                )
                
                # Update the host count in the datacenter
                cursor.execute(
                    "UPDATE datacenters SET n_hosts = n_hosts + 1 WHERE id = %s",
                    (datacenter_id,)
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
                    (host_id,)
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
                    rack_id=result[7]
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
                    (ip,)
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
                    rack_id=result[7]
                )
                
        except Exception as e:
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    
    # UPDATE operations
    def updateHost(self, host_id, name=None, height=None, ip=None, service_id=None, rack_id=None):
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
                    (host_id,)
                )
                host_info = cursor.fetchone()
                
                if host_info is None:
                    return False
                
                current_rack_id = host_info[1]
                current_room_id = host_info[2]
                current_datacenter_id = host_info[3]
                
                # Check if IP is unique if changing it
                if ip is not None:
                    cursor.execute("SELECT id FROM hosts WHERE ip = %s AND id != %s", (ip, host_id))
                    if cursor.fetchone() is not None:
                        raise Exception(f"Host with IP {ip} already exists")
                
                # Check if rack exists and get its room_id and datacenter_id if changing rack
                new_room_id = current_room_id
                new_datacenter_id = current_datacenter_id
                
                if rack_id is not None and rack_id != current_rack_id:
                    cursor.execute("SELECT id, room_id, dc_id FROM racks WHERE id = %s", (rack_id,))
                    rack_info = cursor.fetchone()
                    
                    if rack_info is None:
                        raise Exception(f"Rack with ID {rack_id} does not exist")
                    
                    new_room_id = rack_info[1]
                    new_datacenter_id = rack_info[2]
                
                # Check if service exists (if a new one is provided)
                if service_id is not None:
                    cursor.execute("SELECT id FROM services WHERE id = %s", (service_id,))
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
                        (current_rack_id,)
                    )
                    cursor.execute(
                        "UPDATE rooms SET n_hosts = n_hosts - 1 WHERE id = %s",
                        (current_room_id,)
                    )
                    cursor.execute(
                        "UPDATE datacenters SET n_hosts = n_hosts - 1 WHERE id = %s",
                        (current_datacenter_id,)
                    )
                    
                    # Increment host count in new rack, room, and datacenter
                    cursor.execute(
                        "UPDATE racks SET n_hosts = n_hosts + 1 WHERE id = %s",
                        (rack_id,)
                    )
                    cursor.execute(
                        "UPDATE rooms SET n_hosts = n_hosts + 1 WHERE id = %s",
                        (new_room_id,)
                    )
                    cursor.execute(
                        "UPDATE datacenters SET n_hosts = n_hosts + 1 WHERE id = %s",
                        (new_datacenter_id,)
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
                    (host_id,)
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
                    "UPDATE racks SET n_hosts = n_hosts - 1 WHERE id = %s",
                    (rack_id,)
                )
                
                # Update the host count in the room
                cursor.execute(
                    "UPDATE rooms SET n_hosts = n_hosts - 1 WHERE id = %s",
                    (room_id,)
                )
                
                # Update the host count in the datacenter
                cursor.execute(
                    "UPDATE datacenters SET n_hosts = n_hosts - 1 WHERE id = %s",
                    (datacenter_id,)
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

class ServiceManager:
    """Class for managing service operations"""

    @staticmethod
    def get_connection():
        """Get a connection from the pool"""
        return pool.getconn()

    @staticmethod
    def release_connection(conn):
        """Release a connection back to the pool"""
        pool.putconn(conn)

    # Service operations
    def getService(self, service_id=None):
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
                    cursor.execute("SELECT * FROM services WHERE id = %s", (service_id,))
                    data = cursor.fetchone()
                    if not data:
                        return None
                    
                    # Get racks for this service
                    cursor.execute("SELECT * FROM racks WHERE service_id = %s", (service_id,))
                    racks_data = cursor.fetchall()
                    
                    # Convert to SimpleRack objects
                    racks = []
                    for rack_data in racks_data:
                        rack = SimpleRack(
                            id=rack_data['id'],
                            name=rack_data['name'],
                            room_id=rack_data['room_id'],
                            service_id=rack_data['service_id']
                        )
                        racks.append(rack)
                    
                    # Get IP addresses for this service
                    cursor.execute("SELECT ip_address FROM service_ips WHERE service_id = %s", (service_id,))
                    ip_data = cursor.fetchall()
                    ip_list = [ip['ip_address'] for ip in ip_data]
                    
                    # Create and return a Service object
                    return Service(
                        id=data['id'],
                        name=data['name'],
                        racks=racks,
                        n_racks=data['n_racks'],
                        n_hosts=data['n_hosts'],
                        total_ip=data['total_ip'],
                        ip_list=ip_list
                    )
                else:
                    # Get all services
                    cursor.execute("SELECT * FROM services ORDER BY name")
                    services_data = cursor.fetchall()
                    
                    # Create a list to store Service objects
                    services = []
                    
                    # Process each service
                    for data in services_data:
                        srv_id = data['id']
                        # Get racks for this service
                        cursor.execute("SELECT * FROM racks WHERE service_id = %s", (srv_id,))
                        racks_data = cursor.fetchall()
                        
                        # Convert to SimpleRack objects
                        racks = []
                        for rack_data in racks_data:
                            rack = SimpleRack(
                                id=rack_data['id'],
                                name=rack_data['name'],
                                room_id=rack_data['room_id'],
                                service_id=rack_data['service_id']
                            )
                            racks.append(rack)
                        
                        # Get IP addresses for this service
                        cursor.execute("SELECT ip_address FROM service_ips WHERE service_id = %s", (srv_id,))
                        ip_data = cursor.fetchall()
                        ip_list = [ip['ip_address'] for ip in ip_data]
                        
                        # Create Service object and append to list
                        services.append(
                            Service(
                                id=data['id'],
                                name=data['name'],
                                racks=racks,
                                n_racks=data['n_racks'],
                                n_hosts=data['n_hosts'],
                                total_ip=data['total_ip'],
                                ip_list=ip_list
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

    def createService(self, name, racks=None, ip_list=None):
        """
        Create a new service in the database.
        
        Args:
            name (str): Name of the service
            racks (list[SimpleRack], optional): Racks to assign to this service
            ip_list (list[str], optional): IP addresses to assign to this service
        
        Returns:
            Service: A Service object representing the newly created service.
            None: If creation fails
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Initial rack and IP count
                n_racks = 0
                total_ip = 0
                
                if racks:
                    n_racks = len(racks)
                
                if ip_list:
                    total_ip = len(ip_list)
                
                # Insert the new service
                cursor.execute(
                    """
                    INSERT INTO services (name, n_racks, n_hosts, total_ip)
                    VALUES (%s, %s, 0, %s)
                    RETURNING id, name, n_racks, n_hosts, total_ip
                    """,
                    (name, n_racks, total_ip)
                )
                
                # Get the newly created service data
                new_service = cursor.fetchone()
                
                if not new_service:
                    conn.rollback()
                    return None
                
                service_id = new_service['id']
                
                # Assign racks to this service if provided
                assigned_racks = []
                if racks and len(racks) > 0:
                    for rack in racks:
                        # Check if rack exists
                        cursor.execute("SELECT * FROM racks WHERE id = %s", (rack.id,))
                        rack_data = cursor.fetchone()
                        
                        if rack_data:
                            # Update rack to assign it to this service
                            cursor.execute(
                                "UPDATE racks SET service_id = %s WHERE id = %s RETURNING *",
                                (service_id, rack.id)
                            )
                            updated_rack = cursor.fetchone()
                            
                            if updated_rack:
                                assigned_racks.append(
                                    SimpleRack(
                                        id=updated_rack['id'],
                                        name=updated_rack['name'],
                                        room_id=updated_rack['room_id'],
                                        service_id=updated_rack['service_id']
                                    )
                                )
                
                # Add IP addresses if provided
                assigned_ips = []
                if ip_list and len(ip_list) > 0:
                    for ip in ip_list:
                        # Insert IP address for this service
                        cursor.execute(
                            """
                            INSERT INTO service_ips (service_id, ip_address)
                            VALUES (%s, %s)
                            RETURNING id, service_id, ip_address
                            """,
                            (service_id, ip)
                        )
                        ip_record = cursor.fetchone()
                        
                        if ip_record:
                            assigned_ips.append(ip_record['ip_address'])
                
                # Commit all changes
                conn.commit()
                
                # Create and return a Service object
                return Service(
                    id=service_id,
                    name=new_service['name'],
                    racks=assigned_racks,
                    n_racks=len(assigned_racks),
                    n_hosts=0,  # Initially no hosts
                    total_ip=len(assigned_ips),
                    ip_list=assigned_ips
                )
                
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
                    cursor.execute("UPDATE racks SET service_id = NULL WHERE service_id = %s", (service_id,))
                    
                    # Then assign provided racks to this service
                    n_racks = len(racks)
                    update_parts.append("n_racks = %s")
                    params.append(n_racks)
                    
                    for rack in racks:
                        cursor.execute(
                            "UPDATE racks SET service_id = %s WHERE id = %s",
                            (service_id, rack.id)
                        )
                
                # Handle IP addresses if provided
                if ip_list is not None:
                    # First, delete all existing IP addresses for this service
                    cursor.execute("DELETE FROM service_ips WHERE service_id = %s", (service_id,))
                    
                    # Then add new IP addresses
                    total_ip = len(ip_list)
                    update_parts.append("total_ip = %s")
                    params.append(total_ip)
                    
                    for ip in ip_list:
                        cursor.execute(
                            "INSERT INTO service_ips (service_id, ip_address) VALUES (%s, %s)",
                            (service_id, ip)
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
                cursor.execute("SELECT * FROM racks WHERE service_id = %s", (service_id,))
                racks_data = cursor.fetchall()
                
                # Convert to SimpleRack objects
                updated_racks = []
                for rack_data in racks_data:
                    rack = SimpleRack(
                        id=rack_data['id'],
                        name=rack_data['name'],
                        room_id=rack_data['room_id'],
                        service_id=rack_data['service_id']
                    )
                    updated_racks.append(rack)
                
                # Get updated IP addresses for this service
                cursor.execute("SELECT ip_address FROM service_ips WHERE service_id = %s", (service_id,))
                ip_data = cursor.fetchall()
                updated_ip_list = [ip['ip_address'] for ip in ip_data]
                
                # Commit all changes
                conn.commit()
                
                # Create and return updated Service object
                return Service(
                    id=updated_service['id'],
                    name=updated_service['name'],
                    racks=updated_racks,
                    n_racks=len(updated_racks),
                    n_hosts=updated_service['n_hosts'],
                    total_ip=len(updated_ip_list),
                    ip_list=updated_ip_list
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
                cursor.execute("UPDATE racks SET service_id = NULL WHERE service_id = %s", (service_id,))
                
                # Delete IP addresses for this service
                cursor.execute("DELETE FROM service_ips WHERE service_id = %s", (service_id,))
                
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
                    (service_id, rack_id)
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
                    (service_id, service_id)
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
                    "UPDATE racks SET service_id = NULL WHERE id = %s",
                    (rack_id,)
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
                    (service_id, service_id)
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
                    "INSERT INTO service_ips (service_id, ip_address) VALUES (%s, %s)",
                    (service_id, ip_address)
                )
                
                # Update service IP count
                cursor.execute(
                    """
                    UPDATE services 
                    SET total_ip = (SELECT COUNT(*) FROM service_ips WHERE service_id = %s)
                    WHERE id = %s
                    """,
                    (service_id, service_id)
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
                    "DELETE FROM service_ips WHERE service_id = %s AND ip_address = %s",
                    (service_id, ip_address)
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
                    (service_id, service_id)
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
                    (service_id,)
                )
                
                total_hosts = cursor.fetchone()[0]
                
                # Update service host count
                cursor.execute(
                    "UPDATE services SET n_hosts = %s WHERE id = %s",
                    (total_hosts, service_id)
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

class UserManager:
    """Class for managing User operations"""

    @staticmethod
    def get_connection():
        """Get a connection from the pool"""
        return pool.getconn()

    @staticmethod
    def release_connection(conn):
        """Release a connection back to the pool"""
        pool.putconn(conn)

    # User operations
    def getUser(self, user_id=None, username=None):
        """
        Get user information.
        If user_id or username is provided, returns specific user as User object,
        otherwise returns list of User objects.
        Returns None if user_id/username is provided but not found.
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                if user_id:
                    # Get the specific user by ID
                    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                    data = cursor.fetchone()
                    if not data:
                        return None
                    
                    # Create and return a User object
                    return User(
                        id=data['id'],
                        username=data['username'],
                        password=data['password'],
                        role=data['role']
                    )
                elif username:
                    # Get the specific user by username
                    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
                    data = cursor.fetchone()
                    if not data:
                        return None
                    
                    # Create and return a User object
                    return User(
                        id=data['id'],
                        username=data['username'],
                        password=data['password'],
                        role=data['role']
                    )
                else:
                    # Get all users
                    cursor.execute("SELECT * FROM users ORDER BY username")
                    users_data = cursor.fetchall()
                    
                    # Create a list to store User objects
                    users = []
                    
                    # Process each user
                    for data in users_data:
                        # Create User object and append to list
                        users.append(
                            User(
                                id=data['id'],
                                username=data['username'],
                                password=data['password'],
                                role=data['role']
                            )
                        )
                    
                    return users
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)
    
    def createUser(self, username, password, role):
        """
        Create a new User.
        Returns the created User object or None if creation fails.
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Insert new user
                cursor.execute(
                    "INSERT INTO users (username, password, role) VALUES (%s, %s, %s) RETURNING id",
                    (username, password, role)
                )
                user_id = cursor.fetchone()['id']
                conn.commit()
                
                # Return the new user as a User object
                return self.getUser(user_id)
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)
    
    def updateUser(self, user_id, username=None, password=None, role=None):
        """
        Update an existing User.
        Returns the updated User object or None if update fails.
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                # Prepare update fields
                update_fields = []
                params = []
                
                if username is not None:
                    update_fields.append("username = %s")
                    params.append(username)
                
                if password is not None:
                    update_fields.append("password = %s")
                    params.append(password)
                
                if role is not None:
                    update_fields.append("role = %s")
                    params.append(role)
                
                if not update_fields:
                    return self.getUser(user_id)  # Nothing to update
                
                # Add user_id to params
                params.append(user_id)
                
                # Update the user
                query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
                cursor.execute(query, params)
                conn.commit()
                
                # Return the updated user
                return self.getUser(user_id)
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)
    
    def deleteUser(self, user_id):
        """
        Delete a User.
        Returns True if deletion was successful, False otherwise.
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
                deleted = cursor.rowcount > 0
                conn.commit()
                return deleted
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    def authenticate(self, username, password):
        """
        Authenticate a user.
        Returns the User object if authentication is successful, None otherwise.
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT * FROM users WHERE username = %s AND password = %s",
                    (username, password)
                )
                data = cursor.fetchone()
                if not data:
                    return None
                
                # Create and return a User object
                return User(
                    id=data['id'],
                    username=data['username'],
                    password=data['password'],
                    role=data['role']
                )
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)


# Example usage
    
def test_crud_operations():
    print("Testing CRUD Operations for Datacenter Management System")
    
    # ----- Test UserManager CRUD -----
    print("\n=== Testing UserManager CRUD ===")
    user_manager = UserManager()
    
    # Create
    print("Creating a test user...")
    test_user = user_manager.createUser("testuser", "password123", "normal")
    print(f"Created user: {test_user.username} with ID: {test_user.id}")
    
    # Read
    print("Reading the user...")
    retrieved_user = user_manager.getUser(test_user.id)
    print(f"Retrieved user: {retrieved_user.username}, Role: {retrieved_user.role}")
    
    # Update
    print("Updating the user...")
    updated_user = user_manager.updateUser(test_user.id, role="manager")
    print(f"Updated user: {updated_user.username}, New role: {updated_user.role}")
    
    # ----- Test DatacenterManager CRUD -----
    print("\n=== Testing DatacenterManager CRUD ===")
    datacenter_manager = DatacenterManager()
    
    # Create
    print("Creating a test datacenter...")
    test_dc = datacenter_manager.createDatacenter("Test Datacenter", 42)
    print(f"Created datacenter: {test_dc.name} with ID: {test_dc.id}")
    
    # Read
    print("Reading the datacenter...")
    retrieved_dc = datacenter_manager.getDatacenter(test_dc.id)
    print(f"Retrieved datacenter: {retrieved_dc.name}, Height: {retrieved_dc.height}")
    
    # Update
    print("Updating the datacenter...")
    updated_dc = datacenter_manager.updateDatacenter(test_dc.id, name="Updated Datacenter")
    print(f"Updated datacenter: {updated_dc.name}")
    
    # ----- Test Service and Room Managers -----
    print("\n=== Testing ServiceManager and RoomManager CRUD ===")
    service_manager = ServiceManager()
    room_manager = RoomManager()
    
    # Create service
    test_service = service_manager.createService("Test Service")
    print(f"Created service: {test_service.name} with ID: {test_service.id}")
    
    # Create room
    room_id = room_manager.createRoom("Test Room", 40, test_dc.id)
    print(f"Created room with ID: {room_id}")
    
    # ----- Test RackManager CRUD -----
    print("\n=== Testing RackManager CRUD ===")
    rack_manager = RackManager()
    
    # Create rack
    rack_id = rack_manager.createRack("Test Rack", 42, room_id, test_service.id)
    print(f"Created rack with ID: {rack_id}")
    
    # ----- Test HostManager CRUD -----
    print("\n=== Testing HostManager CRUD ===")
    host_manager = HostManager()
    
    # Create host
    host_id = host_manager.createHost("Test Host", 1, "192.168.1.100", rack_id, test_service.id)
    print(f"Created host with ID: {host_id}")
    
    # ----- Test IPRangeManager CRUD -----
    print("\n=== Testing IPRangeManager CRUD ===")
    ip_range_manager = IPRangeManager()
    
    # Create IP range
    test_ip_range = ip_range_manager.add_ip_range(test_dc.id, "10.0.0.1", "10.0.0.254")
    print(f"Created IP range: {test_ip_range.start_IP} - {test_ip_range.end_IP}")
    
    # ----- Clean Up in Reverse Order -----
    print("\n=== Cleaning Up ===")
    
    # Delete Host
    print("Deleting host...")
    success = host_manager.deleteHost(host_id)
    print(f"Host deleted: {success}")
    
    # Delete Rack
    print("Deleting rack...")
    success = rack_manager.deleteRack(rack_id)
    print(f"Rack deleted: {success}")
    
    # Delete Room
    print("Deleting room...")
    success = room_manager.deleteRoom(room_id)
    print(f"Room deleted: {success}")
    
    # Delete Service
    print("Deleting service...")
    success = service_manager.deleteService(test_service.id)
    print(f"Service deleted: {success}")
    
    # Delete Datacenter
    print("Deleting datacenter...")
    success = datacenter_manager.deleteDatacenter(test_dc.id)
    print(f"Datacenter deleted: {success}")
    
    # Delete User
    print("Deleting user...")
    success = user_manager.deleteUser(test_user.id)
    print(f"User deleted: {success}")
    
    print("\nAll CRUD tests completed!")

if __name__ == "__main__":
    # Test database connection
    test_connection()
    
    # Run CRUD tests
    test_crud_operations()    
