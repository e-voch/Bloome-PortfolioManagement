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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS industries (
            id   INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stocks (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            symbol      VARCHAR(50) NOT NULL,
            name        VARCHAR(255) NOT NULL,
            industry_id INT NOT NULL,
            logo        VARCHAR(255) NOT NULL,
            current_price  DECIMAL(12, 2),
            previous_close DECIMAL(12, 2),
            FOREIGN KEY (industry_id) REFERENCES industries(id) ON DELETE RESTRICT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS holdings (
            user_id INT,
            stock_id INT,
            net_quantity INT,
            avg_cost DECIMAL(12, 2),
            PRIMARY KEY (user_id, stock_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (stock_id) REFERENCES stocks(id) ON DELETE RESTRICT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            stock_id INT,
            type ENUM('BUY', 'SELL'),
            quantity INT,
            price DECIMAL(12, 2),
            date DATE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (stock_id) REFERENCES stocks(id) ON DELETE RESTRICT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INT AUTO_INCREMENT PRIMARY KEY,
            stock_id INT NOT NULL,
            title VARCHAR(500) NOT NULL,
            URL VARCHAR(2000),
            publisher VARCHAR(500),
            published_at DATETIME,
            FOREIGN KEY (stock_id) REFERENCES stocks(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            user_id INT NOT NULL,
            stock_id INT NOT NULL,
            PRIMARY KEY (user_id, stock_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (stock_id) REFERENCES stocks(id) ON DELETE CASCADE
        )
    """)

    conn.commit()

    print("Tables created")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    create_database()
    create_tables()

