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

# Database connection configuration
DB_CONFIG = {
    'dbname': os.environ.get('DB_NAME', 'datacenter_management'),
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', 'password'),
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': os.environ.get('DB_PORT', '5432')
}

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
        If datacenter_id is provided, returns specific datacenter, otherwise returns all.
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                if datacenter_id:
                    cursor.execute("SELECT * FROM datacenters WHERE id = %s", (datacenter_id,))
                    result = cursor.fetchone()
                else:
                    cursor.execute("SELECT * FROM datacenters ORDER BY name")
                    result = cursor.fetchall()
                return result
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    def createDatacenter(self, name, default_height=42):
        """Create a new datacenter"""
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(
                    "INSERT INTO datacenters (name, default_height) VALUES (%s, %s) RETURNING *",
                    (name, default_height)
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

    def updateDatacenter(self, datacenter_id, name=None, default_height=None):
        """Update a datacenter's information"""
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                update_fields = []
                params = []
                
                if name is not None:
                    update_fields.append("name = %s")
                    params.append(name)
                    
                if default_height is not None:
                    update_fields.append("default_height = %s")
                    params.append(default_height)
                
                if not update_fields:
                    return self.getDatacenter(datacenter_id)
                
                params.append(datacenter_id)
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                
                query = f"UPDATE datacenters SET {', '.join(update_fields)} WHERE id = %s RETURNING *"
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

    def deleteDatacenter(self, datacenter_id):
        """Delete a datacenter and all associated resources"""
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM datacenters WHERE id = %s", (datacenter_id,))
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
