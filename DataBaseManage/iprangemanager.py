import ipaddress
import psycopg2.extras
from utils.schema import IP_range
from .connection import BaseManager

class IPRangeManager(BaseManager):
    """Class to manage IP ranges in the database"""
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
                    cursor.execute("SELECT * FROM ip_ranges WHERE dc_id = %s", (datacenter_id,))
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
                    INSERT INTO ip_ranges (dc_id, start_ip, end_ip)
                    VALUES (%s, %s, %s)
                    RETURNING id, dc_id, start_ip, end_ip
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
