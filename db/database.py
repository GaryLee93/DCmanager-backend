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
from utils.schema import DataCenter, Room, Rack, Host

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
                        default_height=data['default_height'],
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
                                default_height=data['default_height'],
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
                        default_height=new_datacenter['default_height'],
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
                        default_height=datacenter['default_height'],
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
                    default_height=updated_datacenter['default_height'],
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
                # First check if rack exists and get its room_id and service_id
                cursor.execute("SELECT id, room_id, service_id FROM racks WHERE id = %s", (rack_id,))
                rack_info = cursor.fetchone()
                
                if rack_info is None:
                    return False
                
                room_id = rack_info[1]
                service_id = rack_info[2]
                
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
                    "UPDATE datacenters SET n_racks = n_racks - 1 WHERE id = (SELECT datacenter_id FROM rooms WHERE id = %s)",
                    (room_id,)
                )
                
                # Update the rack count in the service (if provided)
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
