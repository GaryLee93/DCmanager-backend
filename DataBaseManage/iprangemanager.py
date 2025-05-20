import ipaddress
import psycopg2.extras
from utils.schema import IP_Range
from DataBaseManage.connection import BaseManager


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
                    cursor.execute(
                        "SELECT * FROM ip_ranges WHERE dc_id = %s", (datacenter_id,)
                    )
                else:
                    cursor.execute("SELECT * FROM ip_ranges")

                ip_ranges_data = cursor.fetchall()

                # Convert to IP_Range objects
                ip_ranges = []
                for data in ip_ranges_data:
                    ip_range = IP_Range(
                        start_IP=data["start_ip"], end_IP=data["end_ip"]
                    )
                    ip_ranges.append(ip_range)

                return ip_ranges

        except psycopg2.errors.UndefinedTable as e:
            # TODO: Temporary fix for missing table
            print(e)
            return []

        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    def add_ip_range(self, datacenter_id: str, start_ip: str, end_ip: str) -> IP_Range:
        """
        Add a new IP range to a datacenter.

        Args:
            datacenter_id (str): ID of the datacenter
            start_ip (str): Start IP address
            end_ip (str): End IP address

        Returns:
            IP_Range: The newly created IP range object
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:

                # Validate IP addresses
                start = ipaddress.ip_address(start_ip)
                end = ipaddress.ip_address(end_ip)

                if start.version != end.version:
                    raise ValueError("Start and End IP must be of the same version")

                if start.version == 6 or end.version == 6:
                    raise ValueError("IPv6 is not supported")

                if start > end:
                    raise ValueError("Start IP must be less than or equal to End IP")

                # Check if datacenter exists
                cursor.execute(
                    "SELECT id FROM datacenters WHERE id = %s", (datacenter_id,)
                )
                if cursor.fetchone() is None:
                    raise ValueError(f"Datacenter with ID {datacenter_id} not found")

                # Insert the new IP range
                cursor.execute(
                    """
                    INSERT INTO ip_ranges (dc_id, start_ip, end_ip)
                    VALUES (%s, %s, %s)
                    RETURNING id, dc_id, start_ip, end_ip
                    """,
                    (datacenter_id, start_ip, end_ip),
                )

                # get ips between start and end
                ip_list = [
                    str(ipaddress.IPv4Address(ip))
                    for ip in range(int(start), int(end) + 1)
                ]

                # Insert IP list to service_ips table
                for ip in ip_list:
                    cursor.execute(
                        """
                        INSERT INTO service_ips (ip, dc_id)
                        VALUES (%s, %s)
                        """,
                        (ip, datacenter_id),
                    )

                conn.commit()

                return IP_Range(start_IP=start_ip, end_IP=end_ip)
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)

    def delete_ip_range_under_dc(self, dc_id: str) -> bool:
        """
        Delete all IP ranges under a specific datacenter.

        Args:
            dc_id (str): ID of the datacenter

        Returns:
            bool: True if deleted successfully, False if not found
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM service_ips WHERE dc_id = %s", (dc_id,))
                cursor.execute("DELETE FROM ip_ranges WHERE dc_id = %s", (dc_id,))
                conn.commit()
                return cursor.rowcount > 0

        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.release_connection(conn)
