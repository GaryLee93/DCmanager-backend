import os
import psycopg2
import psycopg2.extras
from utils.schema import DataCenter, Room, Rack, Host, Service, User
from utils.schema import (
    SimpleRoom,
    SimpleRack,
    SimpleService,
    SimpleDataCenter,
)
from DataBaseManage.connection import BaseManager


class UserManager(BaseManager):
    """Class for managing User operations"""
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
                    "INSERT INTO users (username, password, role) VALUES (%s, %s, %s) ",
                    (username, password, role),
                )
                conn.commit()

                # Return the new user as a User object
                return self.getUser(username)
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    # User operations
    def getUser(self, username=None):
        """
        Get user information.
        Returns None if user_id/username is provided but not found.
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                if username:
                    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
                    data = cursor.fetchone()
                    if not data:
                        return None

                    # Create and return a User object
                    return User(
                        username=data["username"],
                        password=data["password"],
                        role=data["role"],
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
                                username=data["username"],
                                password=data["password"],
                                role=data["role"],
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


    def updateUser(self, username, password=None, role=None):
        """
        Update an existing User.
        Returns the updated User object or None if update fails.
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                update_fields = []
                params = []

                # Check if the user exists
                cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()
                if not user:
                    return None
                
                # Prepare the update query
                update_fields.append("username = %s")
                params.append(username)

                # Check if the new username already exists
                cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
                existing_user = cursor.fetchone()
                if existing_user:
                    return None
                
                # Add fields to update
                if password is not None:
                    update_fields.append("password = %s")
                    params.append(password)

                if role is not None:
                    update_fields.append("role = %s")
                    params.append(role)

                # Update the user
                query = f"UPDATE users SET {', '.join(update_fields)} WHERE username = %s"
                params.append(username)
                cursor.execute(query, params)
                conn.commit()

                # Return the updated user
                return self.getUser(username)
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    def deleteUser(self, username):
        """
        Delete a User.
        Returns True if deletion was successful, False otherwise.
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM users WHERE username = %s", (username,))
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
                    (username, password),
                )
                data = cursor.fetchone()
                if not data:
                    return None

                # Create and return a User object
                return User(
                    username=data["username"],
                    password=data["password"],
                    role=data["role"],
                )
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)
