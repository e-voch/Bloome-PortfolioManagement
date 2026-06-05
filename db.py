import mysql.connector
import os

DB_NAME = os.getenv("DB_NAME", "portfolio_database")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
<<<<<<< HEAD
    "password": os.getenv("DB_PASSWORD", "root123"),
=======
    "password": os.getenv("DB_PASSWORD", "root"),
>>>>>>> 944d786df4e0cf408f12a227db9127010e7fe4f0
}


def get_connection(database=None):
    config = DB_CONFIG.copy()
    if database:
        config["database"] = database

    return mysql.connector.connect(**config)
