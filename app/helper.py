from collections import defaultdict
from queries import get_stock_from_ticker
from db import get_connection, DB_NAME 

def generate_stock_allocation_values(holdings, total_value, chart_colours):
    if not holdings:
        return []

    num_holdings = len(holdings)

    stock_weights = [
        {
            "ticker": holdings[i][0], 
            "percentage": round((holdings[i][4] / total_value) * 100, 2), 
            "colour": None
        }
        for i in range(num_holdings)
    ] 

    stock_weights.sort(key=lambda x: x["percentage"], reverse=True)
    
    for i in range(3):
        stock_weights[i]["colour"] = chart_colours[i]

    stock_allocation_chart_values = stock_weights

    if num_holdings > 3:
        other = sum(x["percentage"] for x in stock_weights[3:])
        stock_allocation_chart_values = stock_weights[:3] + [{"ticker": "Other", "percentage": other, "colour": chart_colours[-1]}]

    
    return stock_allocation_chart_values

def generate_industry_allocation_values(holdings, total_value, chart_colours):
    if not holdings:
        return []

    num_holdings = len(holdings)

    industry_values = defaultdict(int)

    conn = get_connection(DB_NAME)

    cursor = conn.cursor(dictionary=True)

    for h in holdings:
        ticker = h[0]

        stock_details = get_stock_from_ticker(cursor, ticker)

        industry_values[stock_details["industry"]] += h[4]

    industry_weights = [
        {
            "industry": industry,
            "percentage": round((value / total_value) * 100, 2),
            "colour": None
        }
        for industry, value in industry_values.items()
    ]
    
    industry_weights.sort(key=lambda x: x["percentage"], reverse=True)
    
    for i in range(3):
        industry_weights[i]["colour"] = chart_colours[i]

    industry_allocation_chart_values = industry_weights

    if num_holdings > 3:
        other = sum(x["percentage"] for x in industry_weights[3:])
        industry_allocation_chart_values = industry_weights[:3] + [{"industry": "Other", "percentage": other, "colour": chart_colours[-1]}]
    
    return industry_allocation_chart_values



        
