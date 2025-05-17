import os
from utils.schema import IP_range, DataCenter, Room, Rack, Host, Service, User
from utils.schema import SimpleRoom, SimpleRack, SimpleHost, SimpleService, SimpleDataCenter
from .connection import BaseManager


class UserManager(BaseManager):
    """Class for managing User operations"""
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

