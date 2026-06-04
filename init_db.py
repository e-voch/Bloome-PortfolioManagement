from db import get_connection, DB_NAME

def create_database():
    conn = get_connection(database=False)
    cursor = conn.cursor()
    
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    
    conn.commit()

    print(f"Database '{DB_NAME}' ready")

    cursor.close()
    conn.close()


def create_tables():
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        DROP TABLE IF EXISTS users
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            is_verified BOOlEAN DEFAULT FALSE,
            verification_token VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()

    print("Tables created")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    create_database()
    create_tables()

