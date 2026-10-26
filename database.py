import os
import mysql.connector
from mysql.connector import Error


def get_connection():
    """Create a MySQL connection using environment-based configuration."""
    try:
        return mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "localhost"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", " "),
            database=os.getenv("MYSQL_DATABASE", "nephrocare"),
        )
    except Error as err:
        print("Database Error:", err)
        return None


if __name__ == "__main__":
    conn = get_connection()
    if conn is not None:
        print("Database Connected Successfully")
        conn.close()
    else:
        print("Database connection failed. Check MySQL service, credentials, and database schema.")
