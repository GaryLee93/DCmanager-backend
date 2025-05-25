# scripts/reset_db.py

import os
import psycopg2
import click

DB_CONFIG = {
    "dbname": os.environ.get("DB_NAME", "datacenter_management"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", "postgres"),
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", "5433")),
}


@click.command()
@click.option('--yes', is_flag=True, help='Confirm reset without prompt')
def reset_db(yes):
    if not yes:
        confirm = input("❗ This will delete all data. Are you sure? (y/N): ")
        if confirm.lower() != 'y':
            print("❌ Canceled.")
            return

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        print("🔄 Resetting tables...")

        cursor.execute("TRUNCATE hosts, racks, ips RESTART IDENTITY CASCADE;")

        conn.commit()
        print("✅ Database reset completed.")

    except Exception as e:
        print("❌ Failed to reset database:", e)

    finally:
        if conn:
            cursor.close()
            conn.close()


if __name__ == '__main__':
    reset_db()
