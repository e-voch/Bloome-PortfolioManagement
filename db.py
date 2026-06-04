import mysql.connector
import os

DB_NAME = os.getenv("DB_NAME", "portfolio_database")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
}


def get_connection(database=None):
    config = DB_CONFIG.copy()
    if database:
        config["database"] = database

    return mysql.connector.connect(**config)

