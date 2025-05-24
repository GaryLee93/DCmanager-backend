import os
import psycopg2
from psycopg2.pool import SimpleConnectionPool

# Database connection configuration
DB_CONFIG = {
    "dbname": os.environ.get("DB_NAME", "datacenter_management"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", "postgres"),
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", "5433")),
}

# Create a connection pool
pool = SimpleConnectionPool(1, 10, **DB_CONFIG)


def test_connection():
    """Test the database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print(f"Connected to database! PostgreSQL version: {version[0]}")
        cur.close()
        conn.close()
        return True  # 返回成功結果
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False  # 返回失敗結果

class BaseManager:
    """Base class with common connection methods"""

    @staticmethod
    def get_connection():
        """Get a connection from the pool"""
        return pool.getconn()

    @staticmethod
    def release_connection(conn):
        """Release a connection back to the pool"""
        pool.putconn(conn)
