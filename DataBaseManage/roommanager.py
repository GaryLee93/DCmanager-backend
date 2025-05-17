import os
from utils.schema import IP_range, DataCenter, Room, Rack, Host, Service, User
from utils.schema import SimpleRoom, SimpleRack, SimpleHost, SimpleService, SimpleDataCenter
from .connection import BaseManager

class RoomManager(BaseManager):  
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
                    "SELECT id, name, height, n_racks, n_hosts, dc_id FROM rooms WHERE id = %s",
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
                cursor.execute("SELECT id, dc_id FROM rooms WHERE id = %s", (room_id,))
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
