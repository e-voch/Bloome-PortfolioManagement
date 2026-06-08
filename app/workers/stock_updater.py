import yfinance as yf
from app.db import get_connection, DB_NAME
from app.queries import add_stock, update_price, update_previous_close

STOCKS_FILE = "./stocks.txt"
STOCK_LIST = open(STOCKS_FILE).read().splitlines()


def get_previous_close():
    conn = get_connection(DB_NAME)
    cursor = conn.cursor(dictionary=True)

    for stock in STOCK_LIST:
        ticker = yf.Ticker(stock)

        previous_close = ticker.info.get('regularMarketPreviousClose') or ticker.info.get('previousClose')

        if previous_close:
            update_previous_close(cursor, stock, previous_close)
            
    conn.commit()
    cursor.close()
    conn.close()


def get_stock_prices():
    conn = get_connection(DB_NAME)
    cursor = conn.cursor(dictionary=True)

    for stock in STOCK_LIST:
        ticker = yf.Ticker(stock)

        current_price = ticker.info.get('currentPrice') or ticker.info.get('regularMarketPrice')

        if current_price:
            update_price(cursor, stock, current_price)
    
    conn.commit()
    cursor.close()
    conn.close()


def populate_stock_table():
    conn = get_connection(DB_NAME)
    cursor = conn.cursor(dictionary=True)

    for stock in STOCK_LIST:
        ticker = yf.Ticker(stock)
        info = ticker.info 

        name = info.get('longName') or info.get('shortName', stock)
        logo = info.get('logo_url', '')
        industry = info.get('sector', 'Unknown')
        
        add_stock(cursor, name, stock, industry, logo)

    conn.commit()
    cursor.close()
    conn.close()


populate_stock_table()
get_stock_prices()
get_previous_close()
