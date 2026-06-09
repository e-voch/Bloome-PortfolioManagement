
def create_user(cursor, username, email, password, token):
    cursor.execute(
        "INSERT INTO users (name, email, password, verification_token) VALUES  (%s, %s, %s, %s)",
        (username, email, password, token)
    )

def get_user_by_email(cursor, email):
    cursor.execute(
        "SELECT * FROM users WHERE email = %s",
        (email,)
    )
    return cursor.fetchone()

def add_stock(cursor, name, ticker, industry, logo):
    cursor.execute(
        "INSERT INTO stocks (symbol, name, industry, logo) VALUES (%s, %s, %s, %s)",
        (ticker, name, industry, logo)
    )

def update_price(cursor, ticker, price):
    cursor.execute(
        "UPDATE stocks SET current_price = %s WHERE symbol = %s",
       (price, ticker)
    )

def update_previous_close(cursor, ticker, previous_close):
    cursor.execute(
        "UPDATE stocks SET previous_close = %s WHERE symbol = %s",
       (previous_close, ticker)
    )

def get_total_value(cursor, user_id):
    cursor.execute(
        """
        SELECT COALESCE(SUM(h.net_quantity * s.current_price), 0)
        FROM holdings h
        INNER JOIN stocks s on s.id = h.stock_id
        WHERE h.user_id = %s
        """,
        (user_id,)
    )
    return cursor.fetchone()[0]

def get_original_investment(cursor, user_id):
    cursor.execute(
        """
        SELECT COALESCE(SUM(avg_cost * net_quantity), 0)
        FROM holdings
        WHERE user_id = %s
        """,
        (user_id,)
    )
    return cursor.fetchone()[0]

def get_daily_gain(cursor, user_id): 
    cursor.execute(
        """
        SELECT COALESCE(SUM((s.current_price - s.previous_close) * h.net_quantity), 0)
        FROM holdings h
        INNER JOIN stocks s ON s.id = h.stock_id
        WHERE h.user_id = %s
        """,
        (user_id,)
    )
    return cursor.fetchone()[0]

def create_transaction(cursor, user_id, stock_id, side, quantity, price, date):
    cursor.execute(
        "INSERT INTO transactions (user_id, stock_id, type, quantity, price, date) VALUES (%s, %s, %s, %s, %s, %s)",
        (user_id, stock_id, side, quantity, price, date)
    )
    
    if side == "BUY":
        cursor.execute(
            """
            INSERT INTO holdings (user_id, stock_id, net_quantity, avg_cost)
            VALUES (%s, %s, %s, %s) AS new
            ON DUPLICATE KEY UPDATE
            avg_cost =
                ((holdings.net_quantity * holdings.avg_cost) + (VALUES(net_quantity) * VALUES(avg_cost)))
                / (holdings.net_quantity + VALUES(net_quantity)),

            net_quantity = holdings.net_quantity + VALUES(net_quantity)
            """,

            (user_id, stock_id, quantity, price)
        )

    elif side == "SELL":
        cursor.execute(
            """
            UPDATE holdings
            SET net_quantity = net_quantity - %s
            WHERE user_id = %s AND stock_id = %s
            """,
            (quantity, user_id, stock_id)
        )

    cursor.execute("DELETE FROM holdings WHERE net_quantity <=0 ")


def get_holdings(cursor, user_id):
    cursor.execute(
        """
        SELECT s.symbol,
               h.net_quantity, 
               h.avg_cost, 
               s.current_price, 
               (h.net_quantity * s.current_price), 
               ((h.net_quantity * s.current_price) - (h.net_quantity * h.avg_cost)),
               h.stock_id
        FROM holdings h
        INNER JOIN stocks s ON s.id = h.stock_id
        WHERE h.user_id = %s
        """,
        (user_id,)
    )

    return cursor.fetchall()


def get_transactions(cursor, user_id):
    cursor.execute(
        """
        SELECT t.date,
               s.symbol, 
               t.type, 
               t.quantity,
               t.price,
               (t.price * t.quantity)
        FROM transactions t
        INNER JOIN stocks s ON s.id = t.stock_id
        WHERE t.user_id = %s
        """,
        (user_id,)
    )

    return cursor.fetchall()

def get_stock_from_ticker(cursor, ticker):
    cursor.execute(
        "SELECT * FROM stocks WHERE symbol = %s",
        (ticker,)
    )

    return cursor.fetchone()

def delete_news_for_stock_id(cursor, stock_id):
    cursor.execute(
        "DELETE FROM news WHERE stock_id = %s",
        (stock_id,)
    )

def create_news_entry(cursor, stock_id, ticker, title, url, publisher, published_at):
    cursor.execute(
        "INSERT INTO news (stock_id, ticker, title, url, publisher, published_at) VALUES  (%s, %s, %s, %s, %s, %s)",
        (stock_id, ticker, title, url, publisher, published_at)
    )


def get_news_for_stock_id(cursor, stock_id):
    cursor.execute(
        "SELECT * FROM news WHERE stock_id = %s",
        (stock_id,)
    )

    return cursor.fetchall()


def update_user_name(cursor, user_id, name):
    cursor.execute(
        "UPDATE users SET name = %s WHERE id = %s",
        (name, user_id)
    )

def update_user_email(cursor, user_id, email):
    cursor.execute(
        "UPDATE users SET email = %s, is_verified = FALSE, verification_token = NULL WHERE id = %s",
        (email, user_id)
    )

def set_verification_token(cursor, user_id, token):
    cursor.execute(
        "UPDATE users SET verification_token = %s WHERE id = %s",
        (token, user_id)
    )

def update_user_password(cursor, user_id, hashed_password):
    cursor.execute(
        "UPDATE users SET password = %s WHERE id = %s",
        (hashed_password, user_id)
    )

def delete_user(cursor, user_id):
    cursor.execute("DELETE FROM holdings WHERE user_id = %s", (user_id,))
    cursor.execute("DELETE FROM transactions WHERE user_id = %s", (user_id,))
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))

def get_watchlist(cursor, user_id):
    cursor.execute("""
        SELECT s.id, s.symbol, s.name, s.current_price,
               COALESCE(s.current_price - s.previous_close, 0) AS price_change,
               CASE WHEN s.previous_close IS NOT NULL AND s.previous_close > 0
                    THEN ROUND(((s.current_price - s.previous_close) / s.previous_close) * 100, 2)
                    ELSE 0
               END AS pct_change
        FROM watchlist w
        JOIN stocks s ON s.id = w.stock_id
        WHERE w.user_id = %s
        ORDER BY s.symbol
    """, (user_id,))
    return cursor.fetchall()

def get_all_stocks(cursor):
    cursor.execute("""
        SELECT s.id, s.symbol, s.name, s.current_price,
               COALESCE(s.current_price - s.previous_close, 0) AS price_change,
               CASE WHEN s.previous_close IS NOT NULL AND s.previous_close > 0
                    THEN ROUND(((s.current_price - s.previous_close) / s.previous_close) * 100, 2)
                    ELSE 0
               END AS pct_change
        FROM stocks s
        ORDER BY s.symbol
    """)
    return cursor.fetchall()

def add_to_watchlist(cursor, user_id, stock_id):
    cursor.execute(
        "INSERT IGNORE INTO watchlist (user_id, stock_id) VALUES (%s, %s)",
        (user_id, stock_id)
    )

def remove_from_watchlist(cursor, user_id, stock_id):
    cursor.execute(
        "DELETE FROM watchlist WHERE user_id = %s AND stock_id = %s",
        (user_id, stock_id)
    )

