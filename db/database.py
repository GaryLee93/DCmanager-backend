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


    # Room operations
    def getRooms(self, datacenter_id=None, room_id=None):
        """
        Get rooms information.
        If datacenter_id is provided, returns list of rooms in that datacenter.
        If room_id is provided, returns specific room as Room object.
        Returns None if room_id is provided but not found.
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                if room_id:
                    # Get the specific room
                    cursor.execute("SELECT * FROM rooms WHERE id = %s", (room_id,))
                    data = cursor.fetchone()
                    if not data:
                        return None
                    
                    # Create and return a Room object
                    # id: str, 
                    #  name: str, 
                    #  height: int, 
                    #  racks: list,
                    #  n_racks: int,
                    #  n_hosts: int,
                    #  dc_id: str

                    return Room(
                        id=data['id'],
                        name=data['name'],
                        height=data['height'],
                        racks=data['racks'],
                        n_racks=data['n_racks'],
                        n_hosts=data['n_hosts'],
                        dc_id=data['datacenter_id']
                    )
                elif datacenter_id:
                    # Get all rooms in the specified datacenter
                    cursor.execute("SELECT * FROM rooms WHERE datacenter_id = %s", (datacenter_id,))
                    rooms_data = cursor.fetchall()
                    
                    # Create a list to store Room objects
                    rooms = []
                    
                    # Process each room
                    for data in rooms_data:
                        # Create Room object and append to list
                        rooms.append(
                            Room(
                                id=data['id'],
                                name=data['name'],
                                height=data['height'],
                                racks=data['racks'],
                                n_racks=data['n_racks'],
                                n_hosts=data['n_hosts'],
                                dc_id=data['datacenter_id']
                            )
                        )
                    
                    return rooms
                else:
                    # Get all rooms
                    cursor.execute("SELECT * FROM rooms ORDER BY name")
                    rooms_data = cursor.fetchall()
                    
                    # Create a list to store Room objects
                    rooms = []
                    
                    # Process each room
                    for data in rooms_data:
                        # Create Room object and append to list
                        rooms.append(
                            Room(
                                id=data['id'],
                                name=data['name'],
                                height=data['height'],
                                racks=data['racks'],
                                n_racks=data['n_racks'],
                                n_hosts=data['n_hosts'],
                                dc_id=data['datacenter_id']
                            )
                        )
                    
                    return rooms
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)
    def createRoom(self, datacenter_id, name, height):
        """
        Create a new room in the specified datacenter.
        
        Args:
            datacenter_id (str): ID of the datacenter
            name (str): Name of the room
            height (int): Height of the room
        
        Returns:
            Room: A Room object representing the newly created room.
            None: If creation fails
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Insert the new room
                cursor.execute(
                    """
                    INSERT INTO rooms (name, height, datacenter_id, n_racks, n_hosts)
                    VALUES (%s, %s, %s, 0, 0)
                    RETURNING id, name, height, n_racks, n_hosts
                    """,
                    (name, height, datacenter_id)
                )
                
                # Commit the transaction
                conn.commit()
                
                # Get the newly created room data
                new_room = cursor.fetchone()
                
                if new_room:
                    # Create and return a Room object
                    return Room(
                        id=new_room['id'],
                        name=new_room['name'],
                        height=new_room['height'],
                        racks=[],  # New room has no racks yet
                        n_racks=new_room['n_racks'],
                        n_hosts=new_room['n_hosts'],
                        dc_id=datacenter_id
                    )
                return None
                
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)
    def updateRoom(self, room_id, name=None, height=None):
        """
        Update an existing room in the database.
        
        Args:
            room_id (str): ID of the room to update
            name (str, optional): New name for the room
            height (int, optional): New height for the room
        
        Returns:
            Room: Updated Room object
            None: If room not found or update fails
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # First check if room exists
                cursor.execute("SELECT * FROM rooms WHERE id = %s", (room_id,))
                room = cursor.fetchone()
                if not room:
                    return None
                
                # Prepare update query parts
                update_parts = []
                params = []
                
                if name is not None:
                    update_parts.append("name = %s")
                    params.append(name)
                    
                if height is not None:
                    update_parts.append("height = %s")
                    params.append(height)
                
                # If no updates requested, return the existing room
                if not update_parts:
                    return Room(
                        id=room['id'],
                        name=room['name'],
                        height=room['height'],
                        racks=room['racks'],
                        n_racks=room['n_racks'],
                        n_hosts=room['n_hosts'],
                        dc_id=room['datacenter_id']
                    )
                
                # Add updated_at to be updated
                update_parts.append("updated_at = CURRENT_TIMESTAMP")
                
                # Build and execute update query
                query = f"UPDATE rooms SET {', '.join(update_parts)} WHERE id = %s RETURNING *"
                params.append(room_id)
                
                cursor.execute(query, params)
                conn.commit()
                
                updated_room = cursor.fetchone()
                
                # Create and return updated Room object
                return Room(
                    id=updated_room['id'],
                    name=updated_room['name'],
                    height=updated_room['height'],
                    racks=updated_room['racks'],
                    n_racks=updated_room['n_racks'],
                    n_hosts=updated_room['n_hosts'],
                    dc_id=room['datacenter_id']
                )
                
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)
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
                # First check if room exists
                cursor.execute("SELECT id FROM rooms WHERE id = %s", (room_id,))
                if cursor.fetchone() is None:
                    return False
                
                # Check if room has any racks (optional: prevent deletion if it has dependencies)
                cursor.execute("SELECT COUNT(*) FROM racks WHERE room_id = %s", (room_id,))
                rack_count = cursor.fetchone()[0]
                
                if rack_count > 0:
                    # You may want to raise a custom exception here instead
                    # to indicate that the room has dependencies
                    raise Exception(f"Cannot delete room with ID {room_id} because it contains {rack_count} racks")
                
                # Delete the room
                cursor.execute("DELETE FROM rooms WHERE id = %s", (room_id,))
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
    # Rack operations
    # id: str, 
    # name: str, 
    # height: int, 
    # hosts: list,
    # n_hosts: int,
    # service_id: str,
    # dc_id: str,
    # room_id: str
    def getRacks(self, datacenter_id=None, room_id=None, rack_id=None):
        """
        Get racks information.
        If datacenter_id is provided, returns list of racks in that datacenter.
        If room_id is provided, returns list of racks in that room.
        If rack_id is provided, returns specific rack as Rack object.
        Returns None if rack_id is provided but not found.
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                if rack_id:
                    # Get the specific rack
                    cursor.execute("SELECT * FROM racks WHERE id = %s", (rack_id,))
                    data = cursor.fetchone()
                    if not data:
                        return None
                    
                    # Create and return a Rack object
                    return Rack(
                        id=data['id'],
                        name=data['name'],
                        height=data['height'],
                        hosts=data['hosts'],
                        n_hosts=data['n_hosts'],
                        service_id=data['service_id'],
                        dc_id=data['datacenter_id'],
                        room_id=data['room_id']
                    )
                elif room_id:
                    # Get all racks in the specified room
                    cursor.execute("SELECT * FROM racks WHERE room_id = %s", (room_id,))
                    racks_data = cursor.fetchall()
                    
                    # Create a list to store Rack objects
                    racks = []
                    
                    # Process each rack
                    for data in racks_data:
                        # Create Rack object and append to list
                        racks.append(
                            Rack(
                                id=data['id'],
                                name=data['name'],
                                height=data['height'],
                                hosts=data['hosts'],
                                n_hosts=data['n_hosts'],
                                service_id=data['service_id'],
                                dc_id=data['datacenter_id'],
                                room_id=data['room_id']
                            )
                        )
                    
                    return racks
                elif datacenter_id:
                    # Get all racks in the specified datacenter
                    cursor.execute("SELECT * FROM racks WHERE datacenter_id = %s", (datacenter_id,))
                    racks_data = cursor.fetchall()
                    
                    # Create a list to store Rack objects
                    racks = []
                    
                    # Process each rack
                    for data in racks_data:
                        # Create Rack object and append to list
                        racks.append(
                            Rack(
                                id=data['id'],
                                name=data['name'],
                                height=data['height'],
                                hosts=data['hosts'],
                                n_hosts=data['n_hosts'],
                                service_id=data['service_id'],
                                dc_id=data['datacenter_id'],
                                room_id=data['room_id']
                            )
                        )
                    return racks
                else:
                    # Get all racks
                    cursor.execute("SELECT * FROM racks ORDER BY name")
                    racks_data = cursor.fetchall()
                    
                    # Create a list to store Rack objects
                    racks = []
                    
                    # Process each rack
                    for data in racks_data:
                        # Create Rack object and append to list
                        racks.append(
                            Rack(
                                id=data['id'],
                                name=data['name'],
                                height=data['height'],
                                hosts=data['hosts'],
                                n_hosts=data['n_hosts'],
                                service_id=data['service_id'],
                                dc_id=data['datacenter_id'],
                                room_id=data['room_id']
                            )
                        )
                    
                    return racks
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)
    def createRack(self, room_id, name, height):
        """
        Create a new rack in the specified room.
        
        Args:
            room_id (str): ID of the room
            name (str): Name of the rack
            height (int): Height of the rack
        
        Returns:
            Rack: A Rack object representing the newly created rack.
            None: If creation fails
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Insert the new rack
                cursor.execute(
                    """
                    INSERT INTO racks (name, height, room_id, n_hosts)
                    VALUES (%s, %s, %s, 0)
                    RETURNING id, name, height, n_hosts
                    """,
                    (name, height, room_id)
                )
                
                # Commit the transaction
                conn.commit()
                
                # Get the newly created rack data
                new_rack = cursor.fetchone()
                
                if new_rack:
                    # Create and return a Rack object
                    return Rack(
                        id=new_rack['id'],
                        name=new_rack['name'],
                        height=new_rack['height'],
                        hosts=[],  # New rack has no hosts yet
                        n_hosts=new_rack['n_hosts'],
                        service_id=None,
                        dc_id=None,
                        room_id=room_id
                    )
                return None
                
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)
    def updateRack(self, rack_id, name=None, height=None):
        """
        Update an existing rack in the database.
        
        Args:
            rack_id (str): ID of the rack to update
            name (str, optional): New name for the rack
            height (int, optional): New height for the rack
        
        Returns:
            Rack: Updated Rack object
            None: If rack not found or update fails
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # First check if rack exists
                cursor.execute("SELECT * FROM racks WHERE id = %s", (rack_id,))
                rack = cursor.fetchone()
                if not rack:
                    return None
                
                # Prepare update query parts
                update_parts = []
                params = []
                
                if name is not None:
                    update_parts.append("name = %s")
                    params.append(name)
                    
                if height is not None:
                    update_parts.append("height = %s")
                    params.append(height)
                
                # If no updates requested, return the existing rack
                if not update_parts:
                    return Rack(
                        id=rack['id'],
                        name=rack['name'],
                        height=rack['height'],
                        hosts=rack['hosts'],
                        n_hosts=rack['n_hosts'],
                        service_id=rack['service_id'],
                        dc_id=rack['datacenter_id'],
                        room_id=rack['room_id']
                    )
                
                # Add updated_at to be updated
                update_parts.append("updated_at = CURRENT_TIMESTAMP")
                
                # Build and execute update query
                query = f"UPDATE racks SET {', '.join(update_parts)} WHERE id = %s RETURNING *"
                params.append(rack_id)
                
                cursor.execute(query, params)
                conn.commit()
                
                updated_rack = cursor.fetchone()
                
                # Create and return updated Rack object
                return Rack(
                    id=updated_rack['id'],
                    name=updated_rack['name'],
                    height=updated_rack['height'],
                    hosts=updated_rack['hosts'],
                    n_hosts=updated_rack['n_hosts'],
                    service_id=updated_rack['service_id'],
                    dc_id=updated_rack['datacenter_id'],
                    room_id=rack['room_id']
                )
                
        except Exception as e:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                self.release_connection(conn)
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
                # First check if rack exists
                cursor.execute("SELECT id FROM racks WHERE id = %s", (rack_id,))
                if cursor.fetchone() is None:
                    return False
                
                # Check if rack has any hosts (optional: prevent deletion if it has dependencies)
                cursor.execute("SELECT COUNT(*) FROM hosts WHERE rack_id = %s", (rack_id,))
                host_count = cursor.fetchone()[0]
                
                if host_count > 0:
                    # You may want to raise a custom exception here instead
                    # to indicate that the rack has dependencies
                    raise Exception(f"Cannot delete rack with ID {rack_id} because it contains {host_count} hosts")
                
                # Delete the rack
                cursor.execute("DELETE FROM racks WHERE id = %s", (rack_id,))
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
if __name__ == '__main__':
    test_connection()
