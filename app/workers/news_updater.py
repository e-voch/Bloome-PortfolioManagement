import yfinance as yf
from app.db import get_connection, DB_NAME
from app.queries import delete_news_for_stock_id, create_news_entry, get_stock_from_ticker

STOCKS_FILE = "./stocks.txt"
STOCK_LIST = open(STOCKS_FILE).read().splitlines()


def get_stock_news(ticker):
    stock = yf.Ticker(ticker)
    news = stock.news

    data = []
    for item in news:
        content = item.get("content", {})

        data.append([
            content.get("title"),
            content.get("canonicalUrl", {}).get("url"),
            content.get("provider", {}).get("displayName"),
            content.get("pubDate")[:-1]
        ])

    return data[:5]


def refresh_news():
    conn = get_connection(DB_NAME)

    cursor = conn.cursor(dictionary=True)

    for ticker in STOCK_LIST:
        stock_data = get_stock_from_ticker(cursor, ticker) 

        stock_id = stock_data['id'] 
                
        delete_news_for_stock_id(cursor, stock_id)
        
        news_data = get_stock_news(ticker)
        
        for article in news_data:
            print(article)
            create_news_entry(cursor, stock_id, stock_data['symbol'], article[0], article[1], article[2], article[3])

    conn.commit()
    cursor.close()
    conn.close()    

refresh_news()

