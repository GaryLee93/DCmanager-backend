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
from utils.schema import DataCenter, Room, Rack, Host, Service, IP_Subnet, User, Company_IP_Subnets

# Database connection configuration
DB_CONFIG = {
    'dbname': os.environ.get('DB_NAME', 'datacenter_management'),
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', 'postgres'),
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': os.environ.get('DB_PORT', '5433')
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
    def getDatacenter(self, datacenter_id=None):
        """
        Get datacenters information.
        If datacenter_id is provided, returns specific datacenter as DataCenter object,
        otherwise returns list of DataCenter objects.
        Returns None if datacenter_id is provided but not found.
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                if datacenter_id:
                    # Get the specific datacenter
                    cursor.execute("SELECT * FROM datacenters WHERE id = %s", (datacenter_id,))
                    data = cursor.fetchone()
                    if not data:
                        return None
                    
                    # Get rooms for this datacenter
                    cursor.execute("SELECT * FROM rooms WHERE datacenter_id = %s", (datacenter_id,))
                    rooms = cursor.fetchall()
                    
                    # Create and return a DataCenter object
                    return DataCenter(
                        id=data['id'],
                        name=data['name'],
                        height=data['default_height'],
                        rooms=rooms,
                        n_rooms=data['n_rooms'],
                        n_racks=data['n_racks'],
                        n_hosts=data['n_hosts']
                    )
                else:
                    # Get all datacenters
                    cursor.execute("SELECT * FROM datacenters ORDER BY name")
                    datacenters_data = cursor.fetchall()
                    
                    # Create a list to store DataCenter objects
                    datacenters = []
                    
                    # Process each datacenter
                    for data in datacenters_data:
                        # Get rooms for this datacenter
                        cursor.execute("SELECT * FROM rooms WHERE datacenter_id = %s", (data['id'],))
                        rooms = cursor.fetchall()
                        
                        # Create DataCenter object and append to list
                        datacenters.append(
                            DataCenter(
                                id=data['id'],
                                name=data['name'],
                                height=data['default_height'],
                                rooms=rooms,
                                n_rooms=data['n_rooms'],
                                n_racks=data['n_racks'],
                                n_hosts=data['n_hosts']
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


    def createDatacenter(self, name, default_height=42):
        """
        Create a new datacenter in the database.
        
        Args:
            name (str): Name of the datacenter
            default_height (int, optional): Default rack height for the datacenter. Defaults to 42.
        
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
                    INSERT INTO datacenters (name, default_height, n_rooms, n_racks, n_hosts)
                    VALUES (%s, %s, 0, 0, 0)
                    RETURNING id, name, default_height, n_rooms, n_racks, n_hosts
                    """,
                    (name, default_height)
                )
                
                # Commit the transaction
                conn.commit()
                
                # Get the newly created datacenter data
                new_datacenter = cursor.fetchone()
                
                if new_datacenter:
                    # Create and return a DataCenter object
                    return DataCenter(
                        id=new_datacenter['id'],
                        name=new_datacenter['name'],
                        height=new_datacenter['default_height'],
                        rooms=[],  # New datacenter has no rooms yet
                        n_rooms=new_datacenter['n_rooms'],
                        n_racks=new_datacenter['n_racks'],
                        n_hosts=new_datacenter['n_hosts']
                    )
                return None
                
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    def updateDatacenter(self, datacenter_id, name=None, default_height=None):
        """
        Update an existing datacenter in the database.
        
        Args:
            datacenter_id (str): ID of the datacenter to update
            name (str, optional): New name for the datacenter
            default_height (int, optional): New default rack height for the datacenter
        
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
                    update_parts.append("default_height = %s")
                    params.append(default_height)
                
                # If no updates requested, return the existing datacenter
                if not update_parts:
                    # Get rooms for this datacenter
                    cursor.execute("SELECT * FROM rooms WHERE datacenter_id = %s", (datacenter_id,))
                    rooms = cursor.fetchall()
                    
                    return DataCenter(
                        id=datacenter['id'],
                        name=datacenter['name'],
                        height=datacenter['default_height'],
                        rooms=rooms,
                        n_rooms=datacenter['n_rooms'],
                        n_racks=datacenter['n_racks'],
                        n_hosts=datacenter['n_hosts']
                    )
                
                # Add updated_at to be updated
                update_parts.append("updated_at = CURRENT_TIMESTAMP")
                
                # Build and execute update query
                query = f"UPDATE datacenters SET {', '.join(update_parts)} WHERE id = %s RETURNING *"
                params.append(datacenter_id)
                
                cursor.execute(query, params)
                conn.commit()
                
                updated_datacenter = cursor.fetchone()
                
                # Get rooms for this datacenter
                cursor.execute("SELECT * FROM rooms WHERE datacenter_id = %s", (datacenter_id,))
                rooms = cursor.fetchall()
                
                # Create and return updated DataCenter object
                return DataCenter(
                    id=updated_datacenter['id'],
                    name=updated_datacenter['name'],
                    height=updated_datacenter['default_height'],
                    rooms=rooms,
                    n_rooms=updated_datacenter['n_rooms'],
                    n_racks=updated_datacenter['n_racks'],
                    n_hosts=updated_datacenter['n_hosts']
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
                
                # Check if datacenter has any rooms (optional: prevent deletion if it has dependencies)
                cursor.execute("SELECT COUNT(*) FROM rooms WHERE datacenter_id = %s", (datacenter_id,))
                room_count = cursor.fetchone()[0]
                
                if room_count > 0:
                    # You may want to raise a custom exception here instead
                    # to indicate that the datacenter has dependencies
                    raise Exception(f"Cannot delete datacenter with ID {datacenter_id} because it contains {room_count} rooms")
                
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


class RoomManager:
    def __init__(self, db_pool):
        """
        Initialize the RoomManager with a database connection pool.
        
        Args:
            db_pool: Database connection pool
        """
        self.db_pool = db_pool
    
    def get_connection(self):
        """Get a connection from the pool"""
        return self.db_pool.getconn()
    
    def release_connection(self, conn):
        """Return a connection to the pool"""
        self.db_pool.putconn(conn)
    
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
                
                # Get racks for this room
                cursor.execute("SELECT id FROM racks WHERE room_id = %s", (room_id,))
                rack_ids = [row[0] for row in cursor.fetchall()]
                
                # Create and return the Room object
                return Room(
                    id=result[0],
                    name=result[1],
                    height=result[2],
                    racks=rack_ids,
                    n_racks=result[3],
                    n_hosts=result[4],
                    dc_id=result[5]
                )
                
        except Exception as e:
            raise e
        finally:
            if conn:
                self.release_connection(conn)
    
    def getRoomsByDatacenter(self, datacenter_id):
        """
        Get all rooms in a specific datacenter.
        
        Args:
            datacenter_id (str): ID of the datacenter
        
        Returns:
            list: List of Room objects
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, name, height, n_racks, n_hosts, datacenter_id FROM rooms WHERE datacenter_id = %s",
                    (datacenter_id,)
                )
                results = cursor.fetchall()
                
                rooms = []
                for result in results:
                    room_id = result[0]
                    
                    # Get racks for this room
                    cursor.execute("SELECT id FROM racks WHERE room_id = %s", (room_id,))
                    rack_ids = [row[0] for row in cursor.fetchall()]
                    
                    # Create Room object
                    room = Room(
                        id=room_id,
                        name=result[1],
                        height=result[2],
                        racks=rack_ids,
                        n_racks=result[3],
                        n_hosts=result[4],
                        dc_id=result[5]
                    )
                    rooms.append(room)
                
                return rooms
                
        except Exception as e:
            raise e
        finally:
            if conn:
                self.release_connection(conn)
    
    def getAllRooms(self):
        """
        Get all rooms.
        
        Returns:
            list: List of Room objects
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, name, height, n_racks, n_hosts, datacenter_id FROM rooms"
                )
                results = cursor.fetchall()
                
                rooms = []
                for result in results:
                    room_id = result[0]
                    
                    # Get racks for this room
                    cursor.execute("SELECT id FROM racks WHERE room_id = %s", (room_id,))
                    rack_ids = [row[0] for row in cursor.fetchall()]
                    
                    # Create Room object
                    room = Room(
                        id=room_id,
                        name=result[1],
                        height=result[2],
                        racks=rack_ids,
                        n_racks=result[3],
                        n_hosts=result[4],
                        dc_id=result[5]
                    )
                    rooms.append(room)
                
                return rooms
                
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
                cursor.execute("SELECT COUNT(*) FROM racks WHERE room_id = %s", (room_id,))
                rack_count = cursor.fetchone()[0]
                
                if rack_count > 0:
                    # You may want to raise a custom exception here instead
                    # to indicate that the room has dependencies
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
    def __init__(self, db_pool):
        """
        Initialize the RackManager with a database connection pool.
        
        Args:
            db_pool: Database connection pool
        """
        self.db_pool = db_pool
    
    def get_connection(self):
        """Get a connection from the pool"""
        return self.db_pool.getconn()
    
    def release_connection(self, conn):
        """Return a connection to the pool"""
        self.db_pool.putconn(conn)
    
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
                cursor.execute("SELECT id, datacenter_id FROM rooms WHERE id = %s", (room_id,))
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
                    "INSERT INTO racks (id, name, height, n_hosts, service_id, datacenter_id, room_id) VALUES (%s, %s, %s, 0, %s, %s, %s)",
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
                    "SELECT id, name, height, n_hosts, service_id, datacenter_id, room_id FROM racks WHERE id = %s",
                    (rack_id,)
                )
                result = cursor.fetchone()
                
                if result is None:
                    return None
                
                # Get hosts for this rack
                cursor.execute("SELECT id FROM hosts WHERE rack_id = %s", (rack_id,))
                host_ids = [row[0] for row in cursor.fetchall()]
                
                # Create and return the Rack object
                return Rack(
                    id=result[0],
                    name=result[1],
                    height=result[2],
                    hosts=host_ids,
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
    
    def getRacksByRoom(self, room_id):
        """
        Get all racks in a specific room.
        
        Args:
            room_id (str): ID of the room
        
        Returns:
            list: List of Rack objects
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, name, height, n_hosts, service_id, datacenter_id, room_id FROM racks WHERE room_id = %s",
                    (room_id,)
                )
                results = cursor.fetchall()
                
                racks = []
                for result in results:
                    rack_id = result[0]
                    
                    # Get hosts for this rack
                    cursor.execute("SELECT id FROM hosts WHERE rack_id = %s", (rack_id,))
                    host_ids = [row[0] for row in cursor.fetchall()]
                    
                    # Create Rack object
                    rack = Rack(
                        id=rack_id,
                        name=result[1],
                        height=result[2],
                        hosts=host_ids,
                        n_hosts=result[3],
                        service_id=result[4],
                        dc_id=result[5],
                        room_id=result[6]
                    )
                    racks.append(rack)
                
                return racks
                
        except Exception as e:
            raise e
        finally:
            if conn:
                self.release_connection(conn)
    
    def getRacksByService(self, service_id):
        """
        Get all racks assigned to a specific service.
        
        Args:
            service_id (str): ID of the service
        
        Returns:
            list: List of Rack objects
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, name, height, n_hosts, service_id, datacenter_id, room_id FROM racks WHERE service_id = %s",
                    (service_id,)
                )
                results = cursor.fetchall()
                
                racks = []
                for result in results:
                    rack_id = result[0]
                    
                    # Get hosts for this rack
                    cursor.execute("SELECT id FROM hosts WHERE rack_id = %s", (rack_id,))
                    host_ids = [row[0] for row in cursor.fetchall()]
                    
                    # Create Rack object
                    rack = Rack(
                        id=rack_id,
                        name=result[1],
                        height=result[2],
                        hosts=host_ids,
                        n_hosts=result[3],
                        service_id=result[4],
                        dc_id=result[5],
                        room_id=result[6]
                    )
                    racks.append(rack)
                
                return racks
                
        except Exception as e:
            raise e
        finally:
            if conn:
                self.release_connection(conn)
    
    def getAllRacks(self):
        """
        Get all racks.
        
        Returns:
            list: List of Rack objects
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, name, height, n_hosts, service_id, datacenter_id, room_id FROM racks"
                )
                results = cursor.fetchall()
                
                racks = []
                for result in results:
                    rack_id = result[0]
                    
                    # Get hosts for this rack
                    cursor.execute("SELECT id FROM hosts WHERE rack_id = %s", (rack_id,))
                    host_ids = [row[0] for row in cursor.fetchall()]
                    
                    # Create Rack object
                    rack = Rack(
                        id=rack_id,
                        name=result[1],
                        height=result[2],
                        hosts=host_ids,
                        n_hosts=result[3],
                        service_id=result[4],
                        dc_id=result[5],
                        room_id=result[6]
                    )
                    racks.append(rack)
                
                return racks
                
        except Exception as e:
            raise e
        finally:
            if conn:
                self.release_connection(conn)
    
    # UPDATE operations
    def updateRack(self, rack_id, name=None, height=None, service_id=None):
        """
        Update a rack's information.
        
        Args:
            rack_id (str): ID of the rack to update
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
                cursor.execute("SELECT id, room_id, datacenter_id, service_id FROM racks WHERE id = %s", (rack_id,))
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
    def __init__(self, db_pool):
        """
        Initialize the HostManager with a database connection pool.
        
        Args:
            db_pool: Database connection pool
        """
        self.db_pool = db_pool
    
    def get_connection(self):
        """Get a connection from the pool"""
        return self.db_pool.getconn()
    
    def release_connection(self, conn):
        """Return a connection to the pool"""
        self.db_pool.putconn(conn)
    
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
                cursor.execute("SELECT id, room_id, datacenter_id FROM racks WHERE id = %s", (rack_id,))
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
                    "INSERT INTO hosts (id, name, height, ip, service_id, datacenter_id, room_id, rack_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
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
                    "SELECT id, name, height, ip, service_id, datacenter_id, room_id, rack_id FROM hosts WHERE id = %s",
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
                    "SELECT id, name, height, ip, service_id, datacenter_id, room_id, rack_id FROM hosts WHERE ip = %s",
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
    
    def getHostsByRack(self, rack_id):
        """
        Get all hosts in a specific rack.
        
        Args:
            rack_id (str): ID of the rack
        
        Returns:
            list: List of Host objects
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, name, height, ip, service_id, datacenter_id, room_id, rack_id FROM hosts WHERE rack_id = %s",
                    (rack_id,)
                )
                results = cursor.fetchall()
                
                hosts = []
                for result in results:
                    host = Host(
                        id=result[0],
                        name=result[1],
                        height=result[2],
                        ip=result[3],
                        service_id=result[4],
                        dc_id=result[5],
                        room_id=result[6],
                        rack_id=result[7]
                    )
                    hosts.append(host)
                
                return hosts
                
        except Exception as e:
            raise e
        finally:
            if conn:
                self.release_connection(conn)
    
    def getHostsByService(self, service_id):
        """
        Get all hosts assigned to a specific service.
        
        Args:
            service_id (str): ID of the service
        
        Returns:
            list: List of Host objects
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, name, height, ip, service_id, datacenter_id, room_id, rack_id FROM hosts WHERE service_id = %s",
                    (service_id,)
                )
                results = cursor.fetchall()
                
                hosts = []
                for result in results:
                    host = Host(
                        id=result[0],
                        name=result[1],
                        height=result[2],
                        ip=result[3],
                        service_id=result[4],
                        dc_id=result[5],
                        room_id=result[6],
                        rack_id=result[7]
                    )
                    hosts.append(host)
                
                return hosts
                
        except Exception as e:
            raise e
        finally:
            if conn:
                self.release_connection(conn)
    
    def getAllHosts(self):
        """
        Get all hosts.
        
        Returns:
            list: List of Host objects
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, name, height, ip, service_id, datacenter_id, room_id, rack_id FROM hosts"
                )
                results = cursor.fetchall()
                
                hosts = []
                for result in results:
                    host = Host(
                        id=result[0],
                        name=result[1],
                        height=result[2],
                        ip=result[3],
                        service_id=result[4],
                        dc_id=result[5],
                        room_id=result[6],
                        rack_id=result[7]
                    )
                    hosts.append(host)
                
                return hosts
                
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
                    "SELECT id, rack_id, room_id, datacenter_id FROM hosts WHERE id = %s",
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
                    cursor.execute("SELECT id, room_id, datacenter_id FROM racks WHERE id = %s", (rack_id,))
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
                    query_parts.append("datacenter_id = %s")
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
                    "SELECT id, rack_id, room_id, datacenter_id FROM hosts WHERE id = %s",
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
    def __init__(self, db_pool):
        """
        Initialize the ServiceManager with a database connection pool.
        
        Args:
            db_pool: Database connection pool
        """
        self.db_pool = db_pool
    
    def get_connection(self):
        """Get a connection from the pool"""
        return self.db_pool.getconn()
    
    def release_connection(self, conn):
        """Return a connection to the pool"""
        self.db_pool.putconn(conn)
    
    # CREATE operations
    def createService(self, name, subnet_ip, subnet_mask):
        """
        Create a new service.
        
        Args:
            name (str): Name of the service
            subnet_ip (str): IP address of the subnet
            subnet_mask (int): Subnet mask
        
        Returns:
            str: ID of the newly created service
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                # Generate a new UUID for the service
                cursor.execute("SELECT gen_random_uuid()")
                service_id = cursor.fetchone()[0]
                
                # Insert the new service
                cursor.execute(
                    "INSERT INTO services (id, name, n_racks, subnet_ip, subnet_mask) VALUES (%s, %s, 0, %s, %s)",
                    (service_id, name, subnet_ip, subnet_mask)
                )
                conn.commit()
                return service_id
                
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)
    
    # READ operations
    def getService(self, service_id):
        """
        Get a service by ID.
        
        Args:
            service_id (str): ID of the service to retrieve
        
        Returns:
            Service: Service object if found, None otherwise
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, name, n_racks, subnet_ip, subnet_mask FROM services WHERE id = %s",
                    (service_id,)
                )
                result = cursor.fetchone()
                
                if result is None:
                    return None
                
                # Get racks for this service
                cursor.execute("SELECT id FROM racks WHERE service_id = %s", (service_id,))
                rack_ids = [row[0] for row in cursor.fetchall()]
                
                # Create the IP_Subnet object
                subnet = IP_Subnet(
                    ip=result[3],
                    mask=result[4]
                )
                
                # Create and return the Service object
                return Service(
                    id=result[0],
                    name=result[1],
                    racks=rack_ids,
                    n_racks=result[2],
                    subnet=subnet
                )
                
        except Exception as e:
            raise e
        finally:
            if conn:
                self.release_connection(conn)
    
    def getServiceByName(self, name):
        """
        Get a service by name.
        
        Args:
            name (str): Name of the service to retrieve
        
        Returns:
            Service: Service object if found, None otherwise
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, name, n_racks, subnet_ip, subnet_mask FROM services WHERE name = %s",
                    (name,)
                )
                result = cursor.fetchone()
                
                if result is None:
                    return None
                
                service_id = result[0]
                
                # Get racks for this service
                cursor.execute("SELECT id FROM racks WHERE service_id = %s", (service_id,))
                rack_ids = [row[0] for row in cursor.fetchall()]
                
                # Create the IP_Subnet object
                subnet = IP_Subnet(
                    ip=result[3],
                    mask=result[4]
                )
                
                # Create and return the Service object
                return Service(
                    id=service_id,
                    name=result[1],
                    racks=rack_ids,
                    n_racks=result[2],
                    subnet=subnet
                )
                
        except Exception as e:
            raise e
        finally:
            if conn:
                self.release_connection(conn)
    
    def getAllServices(self):
        """
        Get all services.
        
        Returns:
            list: List of Service objects
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, name, n_racks, subnet_ip, subnet_mask FROM services"
                )
                results = cursor.fetchall()
                
                services = []
                for result in results:
                    service_id = result[0]
                    
                    # Get racks for this service
                    cursor.execute("SELECT id FROM racks WHERE service_id = %s", (service_id,))
                    rack_ids = [row[0] for row in cursor.fetchall()]
                    
                    # Create the IP_Subnet object
                    subnet = IP_Subnet(
                        ip=result[3],
                        mask=result[4]
                    )
                    
                    # Create Service object
                    service = Service(
                        id=service_id,
                        name=result[1],
                        racks=rack_ids,
                        n_racks=result[2],
                        subnet=subnet
                    )
                    services.append(service)
                
                return services
                
        except Exception as e:
            raise e
        finally:
            if conn:
                self.release_connection(conn)
    
    # UPDATE operations
    def updateService(self, service_id, name=None, subnet_ip=None, subnet_mask=None):
        """
        Update a service's information.
        
        Args:
            service_id (str): ID of the service to update
            name (str, optional): New name for the service
            subnet_ip (str, optional): New subnet IP for the service
            subnet_mask (int, optional): New subnet mask for the service
        
        Returns:
            bool: True if service was successfully updated, False if not found
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                # First check if service exists
                cursor.execute("SELECT id FROM services WHERE id = %s", (service_id,))
                if cursor.fetchone() is None:
                    return False
                
                # Build the update query based on provided parameters
                update_params = []
                query_parts = []
                
                if name is not None:
                    query_parts.append("name = %s")
                    update_params.append(name)
                
                if subnet_ip is not None:
                    query_parts.append("subnet_ip = %s")
                    update_params.append(subnet_ip)
                
                if subnet_mask is not None:
                    query_parts.append("subnet_mask = %s")
                    update_params.append(subnet_mask)
                
                if not query_parts:
                    # Nothing to update
                    return True
                
                query = f"UPDATE services SET {', '.join(query_parts)} WHERE id = %s"
                update_params.append(service_id)
                
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
                
                # Check if service has any racks or hosts assigned to it
                cursor.execute("SELECT COUNT(*) FROM racks WHERE service_id = %s", (service_id,))
                rack_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM hosts WHERE service_id = %s", (service_id,))
                host_count = cursor.fetchone()[0]
                
                if rack_count > 0 or host_count > 0:
                    # You may want to raise a custom exception here instead
                    # to indicate that the service has dependencies
                    raise Exception(f"Cannot delete service with ID {service_id} because it has {rack_count} racks and {host_count} hosts assigned to it")
                
                # Delete the service
                cursor.execute("DELETE FROM services WHERE id = %s", (service_id,))
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

class IP_SubnetManager:
    """Class for managing IP Subnet operations"""

    @staticmethod
    def get_connection():
        """Get a connection from the pool"""
        return pool.getconn()

    @staticmethod
    def release_connection(conn):
        """Release a connection back to the pool"""
        pool.putconn(conn)

    # IP Subnet operations
    def getIP_Subnet(self, subnet_id=None):
        """
        Get IP Subnet information.
        If subnet_id is provided, returns specific IP Subnet as IP_Subnet object,
        otherwise returns list of IP_Subnet objects.
        Returns None if subnet_id is provided but not found.
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                if subnet_id:
                    # Get the specific subnet
                    cursor.execute("SELECT * FROM ip_subnets WHERE id = %s", (subnet_id,))
                    data = cursor.fetchone()
                    if not data:
                        return None
                    
                    # Create and return an IP_Subnet object
                    return IP_Subnet(
                        ip=data['ip'],
                        mask=data['mask']
                    )
                else:
                    # Get all subnets
                    cursor.execute("SELECT * FROM ip_subnets ORDER BY ip")
                    subnets_data = cursor.fetchall()
                    
                    # Create a list to store IP_Subnet objects
                    subnets = []
                    
                    # Process each subnet
                    for data in subnets_data:
                        # Create IP_Subnet object and append to list
                        subnets.append(
                            IP_Subnet(
                                ip=data['ip'],
                                mask=data['mask']
                            )
                        )
                    
                    return subnets
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)
    
    def createIP_Subnet(self, ip, mask):
        """
        Create a new IP Subnet.
        Returns the created IP_Subnet object or None if creation fails.
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Insert new subnet
                cursor.execute(
                    "INSERT INTO ip_subnets (ip, mask) VALUES (%s, %s) RETURNING id",
                    (ip, mask)
                )
                subnet_id = cursor.fetchone()['id']
                conn.commit()
                
                # Return the new subnet as an IP_Subnet object
                return self.getIP_Subnet(subnet_id)
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)
    
    def updateIP_Subnet(self, subnet_id, ip=None, mask=None):
        """
        Update an existing IP Subnet.
        Returns the updated IP_Subnet object or None if update fails.
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                # Prepare update fields
                update_fields = []
                params = []
                
                if ip is not None:
                    update_fields.append("ip = %s")
                    params.append(ip)
                
                if mask is not None:
                    update_fields.append("mask = %s")
                    params.append(mask)
                
                if not update_fields:
                    return self.getIP_Subnet(subnet_id)  # Nothing to update
                
                # Add subnet_id to params
                params.append(subnet_id)
                
                # Update the subnet
                query = f"UPDATE ip_subnets SET {', '.join(update_fields)} WHERE id = %s"
                cursor.execute(query, params)
                conn.commit()
                
                # Return the updated subnet
                return self.getIP_Subnet(subnet_id)
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)
    
    def deleteIP_Subnet(self, subnet_id):
        """
        Delete an IP Subnet.
        Returns True if deletion was successful, False otherwise.
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM ip_subnets WHERE id = %s", (subnet_id,))
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


class Company_IP_SubnetsManager:
    """Class for managing Company IP Subnets operations"""

    @staticmethod
    def get_connection():
        """Get a connection from the pool"""
        return pool.getconn()

    @staticmethod
    def release_connection(conn):
        """Release a connection back to the pool"""
        pool.putconn(conn)

    # Company IP Subnets operations
    def getCompany_IP_Subnets(self, company_id):
        """
        Get Company IP Subnets information.
        Returns Company_IP_Subnets object for the specified company.
        Returns None if company_id is not found.
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Check if company exists
                cursor.execute("SELECT * FROM companies WHERE id = %s", (company_id,))
                if not cursor.fetchone():
                    return None
                
                # Get all IP subnets for this company
                cursor.execute(
                    "SELECT ip_subnets.* FROM company_ip_subnets " +
                    "JOIN ip_subnets ON company_ip_subnets.subnet_id = ip_subnets.id " +
                    "WHERE company_ip_subnets.company_id = %s",
                    (company_id,)
                )
                subnets_data = cursor.fetchall()
                
                # Create a list to store IP_Subnet objects
                ip_subnets = []
                
                # Process each subnet
                for data in subnets_data:
                    # Create IP_Subnet object and append to list
                    ip_subnets.append(
                        IP_Subnet(
                            ip=data['ip'],
                            mask=data['mask']
                        )
                    )
                
                # Create and return a Company_IP_Subnets object
                return Company_IP_Subnets(ip_subnets=ip_subnets)
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)
    
    def addSubnetToCompany(self, company_id, subnet_id):
        """
        Add an IP Subnet to a Company.
        Returns True if addition was successful, False otherwise.
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                # Check if the association already exists
                cursor.execute(
                    "SELECT * FROM company_ip_subnets WHERE company_id = %s AND subnet_id = %s",
                    (company_id, subnet_id)
                )
                if cursor.fetchone():
                    return True  # Association already exists
                
                # Add the association
                cursor.execute(
                    "INSERT INTO company_ip_subnets (company_id, subnet_id) VALUES (%s, %s)",
                    (company_id, subnet_id)
                )
                conn.commit()
                return True
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)
    
    def removeSubnetFromCompany(self, company_id, subnet_id):
        """
        Remove an IP Subnet from a Company.
        Returns True if removal was successful, False otherwise.
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM company_ip_subnets WHERE company_id = %s AND subnet_id = %s",
                    (company_id, subnet_id)
                )
                removed = cursor.rowcount > 0
                conn.commit()
                return removed
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)

# Example usage
def main():
    # Create a DatacenterManager instance
    manager = DatacenterManager()
    # Create a new datacenter
    new_dc = manager.createDatacenter("New Datacenter", 42)
    print(f"Created Datacenter: {new_dc.name} with ID: {new_dc.id}")
    # Get all datacenters
    all_dcs = manager.getDatacenter()
    print("All Datacenters:")
    for dc in all_dcs:
        print(f"Datacenter ID: {dc.id}, Name: {dc.name}")
    
if __name__ == '__main__':
    test_connection()
