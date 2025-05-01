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
            """Get rooms based on datacenter_id or room_id"""
            conn = None
            try:
                conn = self.get_connection()
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    if room_id:
                        cursor.execute("SELECT * FROM rooms WHERE id = %s", (room_id,))
                        return cursor.fetchone()
                    elif datacenter_id:
                        cursor.execute("SELECT * FROM rooms WHERE dc_id = %s ORDER BY name", (datacenter_id,))
                        return cursor.fetchall()
                    else:
                        cursor.execute("SELECT * FROM rooms ORDER BY name")
                        return cursor.fetchall()
            except Exception as e:
                if conn:
                    conn.rollback()
                raise e
            finally:
                if conn:
                    self.release_connection(conn)

        def createRoom(self, name, dc_id, height=None):
            """Create a new room in a datacenter"""
            conn = None
            try:
                conn = self.get_connection()
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    # Get datacenter's default height if not specified
                    if height is None:
                        cursor.execute("SELECT default_height FROM datacenters WHERE id = %s", (dc_id,))
                        datacenter = cursor.fetchone()
                        if not datacenter:
                            raise ValueError(f"Datacenter with id {dc_id} not found")
                        height = datacenter['default_height']
                    
                    cursor.execute(
                        "INSERT INTO rooms (name, dc_id, height) VALUES (%s, %s, %s) RETURNING *",
                        (name, dc_id, height)
                    )
                    conn.commit()
                    return cursor.fetchone()
            except Exception as e:
                if conn:
                    conn.rollback()
                raise e
            finally:
                if conn:
                    self.release_connection(conn)

        def updateRoom(self, room_id, name=None, height=None):
            """Update a room's information"""
            conn = None
            try:
                conn = self.get_connection()
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    update_fields = []
                    params = []
                    
                    if name is not None:
                        update_fields.append("name = %s")
                        params.append(name)
                        
                    if height is not None:
                        update_fields.append("height = %s")
                        params.append(height)
                    
                    if not update_fields:
                        return self.getRooms(room_id=room_id)
                    
                    params.append(room_id)
                    update_fields.append("updated_at = CURRENT_TIMESTAMP")
                    
                    query = f"UPDATE rooms SET {', '.join(update_fields)} WHERE id = %s RETURNING *"
                    cursor.execute(query, params)
                    conn.commit()
                    return cursor.fetchone()
            except Exception as e:
                if conn:
                    conn.rollback()
                raise e
            finally:
                if conn:
                    self.release_connection(conn)

        def deleteRoom(self, room_id):
            """Delete a room and all associated resources"""
            conn = None
            try:
                conn = self.get_connection()
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM rooms WHERE id = %s", (room_id,))
                    deleted_rows = cursor.rowcount
                    conn.commit()
                    return deleted_rows > 0
            except Exception as e:
                if conn:
                    conn.rollback()
                raise e
            finally:
                if conn:
                    self.release_connection(conn)

        # Rack operations
        def getRacks(self, datacenter_id=None, room_id=None, rack_id=None):
            """Get racks based on datacenter_id, room_id, or rack_id"""
            conn = None
            try:
                conn = self.get_connection()
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    if rack_id:
                        cursor.execute("SELECT * FROM racks WHERE id = %s", (rack_id,))
                        return cursor.fetchone()
                    elif room_id:
                        cursor.execute("SELECT * FROM racks WHERE room_id = %s ORDER BY name", (room_id,))
                        return cursor.fetchall()
                    elif datacenter_id:
                        cursor.execute("SELECT * FROM racks WHERE dc_id = %s ORDER BY name", (datacenter_id,))
                        return cursor.fetchall()
                    else:
                        cursor.execute("SELECT * FROM racks ORDER BY name")
                        return cursor.fetchall()
            except Exception as e:
                if conn:
                    conn.rollback()
                raise e
            finally:
                if conn:
                    self.release_connection(conn)

        def createRack(self, name, room_id, height=42):
            """Create a new rack in a room"""
            conn = None
            try:
                conn = self.get_connection()
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    # Get datacenter ID for the given room
                    cursor.execute("SELECT dc_id FROM rooms WHERE id = %s", (room_id,))
                    room = cursor.fetchone()
                    if not room:
                        raise ValueError(f"Room with id {room_id} not found")
                    
                    cursor.execute(
                        "INSERT INTO racks (name, room_id, dc_id, height) VALUES (%s, %s, %s, %s) RETURNING *",
                        (name, room_id, room['dc_id'], height)
                    )
                    conn.commit()
                    return cursor.fetchone()
            except Exception as e:
                if conn:
                    conn.rollback()
                raise e
            finally:
                if conn:
                    self.release_connection(conn)

        def updateRack(self, rack_id, name=None, room_id=None, height=None):
            """Update a rack's information"""
            conn = None
            try:
                conn = self.get_connection()
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    update_fields = []
                    params = []
                    
                    if name is not None:
                        update_fields.append("name = %s")
                        params.append(name)
                    
                    if height is not None:
                        update_fields.append("height = %s")
                        params.append(height)
                    
                    if room_id is not None:
                        # Get datacenter ID for the new room
                        cursor.execute("SELECT dc_id FROM rooms WHERE id = %s", (room_id,))
                        room = cursor.fetchone()
                        if not room:
                            raise ValueError(f"Room with id {room_id} not found")
                        
                        update_fields.append("room_id = %s")
                        params.append(room_id)
                        update_fields.append("dc_id = %s")
                        params.append(room['dc_id'])
                    
                    if not update_fields:
                        return self.getRacks(rack_id=rack_id)
                    
                    params.append(rack_id)
                    update_fields.append("updated_at = CURRENT_TIMESTAMP")
                    
                    query = f"UPDATE racks SET {', '.join(update_fields)} WHERE id = %s RETURNING *"
                    cursor.execute(query, params)
                    conn.commit()
                    return cursor.fetchone()
            except Exception as e:
                if conn:
                    conn.rollback()
                raise e
            finally:
                if conn:
                    self.release_connection(conn)

        def deleteRack(self, rack_id):
            """Delete a rack and all associated hosts"""
            conn = None
            try:
                conn = self.get_connection()
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM racks WHERE id = %s", (rack_id,))
                    deleted_rows = cursor.rowcount
                    conn.commit()
                    return deleted_rows > 0
            except Exception as e:
                if conn:
                    conn.rollback()
                raise e
            finally:
                if conn:
                    self.release_connection(conn)

    if __name__ == '__main__':
        test_connection()
