
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
               (t.price * t.quantity),
               t.id
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


def delete_transaction(cursor, transaction_id):
    cursor.execute(
        "DELETE FROM transactions WHERE id = %s",
        (transaction_id,)
    )


def recompute_holding(cursor, user_id, stock_id):
    print(user_id, stock_id)
    cursor.execute(
        """
        SELECT type, quantity, price
        FROM transactions
        WHERE user_id = %s AND stock_id = %s
        ORDER BY date, id
        """,
        (user_id, stock_id)
    )

    quantity = 0
    cost = 0

    for transaction in cursor.fetchall():
        if transaction["type"] == "BUY":
            quantity += transaction["quantity"]
            cost += transaction["price"]
        elif transaction["type"] == "SELL":
            quantity -= transaction["quantity"]

    cursor.execute(
        "DELETE FROM holdings WHERE user_id = %s and stock_id = %s",
        (user_id, stock_id)
    )

    if quantity > 0:
        avg_price = (cost / quantity)

        cursor.execute(
            """
            INSERT INTO holdings (user_id, stock_id, net_quantity, avg_cost)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, stock_id, quantity, avg_price)
        )

def get_transaction(cursor, transaction_id):
    print(transaction_id)
    cursor.execute(
        "SELECT * FROM transactions WHERE id = %s",
        (transaction_id,)
    )

    return cursor.fetchone()
