import secrets
from flask import Blueprint, request, render_template, redirect, session
from queries import create_user, get_user_by_email, get_total_value, get_daily_gain, get_original_investment, get_holdings, get_transactions, create_transaction, get_stock_from_ticker
from db import get_connection, DB_NAME
from werkzeug.security import generate_password_hash, check_password_hash
from mail import send_verification_email

routes = Blueprint("routes", __name__)


@routes.route("/")
def home():
    return render_template("landing.html")

"""
LOGIN PAGE (GET)
"""
@routes.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")

"""
SIGNUP PAGE (GET)
"""
@routes.route("/signup", methods=["GET"])
def signup_page():
    return render_template("signup.html")


"""
HANDLES LOGIN LOGIC
"""
@routes.route("/login", methods=["POST"])
def login():
    print("request recieved")
    email = request.form["email"]
    password = request.form["password"]
    
    conn = get_connection(DB_NAME)
    cursor = conn.cursor(dictionary=True)

    user = get_user_by_email(cursor, email) 
    
    if not user or not check_password_hash(user["password"], password):
        return {"error": "Invalid email or password"}, 401
    
    if not user["is_verified"]:
        return {"error" : "Please verify your email first"}, 403

    session["user_id"] = user["id"]
    session["name"] = user["name"]
    
    print("user logged in")

    return redirect("/dashboard")
    
"""
HANDLES SIGNUP LOGIC
"""
@routes.route("/signup", methods=["POST"])
def signup():
    name = request.form["name"]
    email = request.form["email"]
    password = request.form["password"]
    
    hashed_password = generate_password_hash(password)
    token = secrets.token_urlsafe(32)

    conn = get_connection(DB_NAME)
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users where email = %s", (email,))
    existing_user = cursor.fetchone()

    if existing_user:
        cursor.close()
        conn.close()
        return "User already exists", 409

    create_user(cursor, name, email, hashed_password, token)

    conn.commit()

    cursor.close()
    conn.close()

    send_verification_email(email, token)

    return redirect("/signup")
    
"""
HANDLES EMAIL VERIFICATION
"""
@routes.route("/verify/<token>")
def verify_token(token):
    conn = get_connection(DB_NAME)

    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id FROM users WHERE verification_token = %s
    """, (token,))

    user = cursor.fetchone()

    if not user:
        return "Invalid token", 400

    cursor.execute("""
        UPDATE users
        SET is_verified = TRUE,
            verification_token = NULL
        WHERE id = %s
    """, (user['id'],))

    conn.commit()
    cursor.close()
    conn.close()

    return "Email verified successfully!"

"""
HANDLES DASHBOARD PAGE
"""
@routes.route("/dashboard")
def dashboard():
    conn = get_connection(DB_NAME)

    cursor = conn.cursor()

    total_value = get_total_value(cursor, session.get("user_id"))
    day_change = get_daily_gain(cursor, session.get("user_id")) 
    total_investment = get_original_investment(cursor, session.get("user_id")) 

    total_gain = total_value - total_investment
    day_change_percentage = round((day_change / total_value) * 100) if total_value else 0
    total_return_percentage = round((total_gain / total_investment) * 100) if total_investment else 0

    conn.commit()
    cursor.close()
    conn.close()

    return render_template(
         "dashboard.html",
         name = session.get("name"),
         total_value=total_value,
         day_change=day_change,
         total_gain=total_gain,
         day_change_percentage=day_change_percentage,
         total_return_percentage=total_return_percentage
    )

"""
HANDLES HOLDINGS PAGE
"""
@routes.route("/holdings")
def holdings():
    conn = get_connection(DB_NAME)

    cursor = conn.cursor()
    
    data = get_holdings(cursor, session.get("user_id"))

    holdings = []

    total_value = sum(row[4] for row in data)
    total_earnings = sum(row[5] for row in data)


    holdings = [list(row) + [round((row[4] / total_value) * 100, 2)] for row in data] 

    conn.commit()
    cursor.close()
    conn.close()

    return render_template(
        "holdings.html",
        name = session.get("name"),
        holdings=holdings,
        total_value=total_value,
        total_earnings=total_earnings
    )

"""
Handles TRANSACTIONS PAGE
"""
@routes.route("/transactions")
def transactions():
    conn = get_connection(DB_NAME)

    cursor = conn.cursor()

    transactions = get_transactions(cursor, session.get("user_id"))
    
    conn.commit()
    cursor.close()
    conn.close()

    return render_template(
        "transactions.html",
        transactions = transactions,
        name = session.get("name")
    )


"""
ADDS TRANSACTION
"""
@routes.route("/add_transaction", methods = ["POST"])
def add_transaction():
    conn = get_connection(DB_NAME)

    cursor = conn.cursor(dictionary=True)

    ticker = request.form.get("ticker") 
    side = request.form.get("type") 
    date = request.form.get("date") 
    shares = request.form.get("shares") 
    price = request.form.get("price") 

    user_id = session.get("user_id")
    stock_id = get_stock_from_ticker(cursor, ticker)['id']

    create_transaction(cursor, user_id, stock_id, side, shares, price, date)
   
    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/transactions")


"""
NEWS PAGE
"""
@routes.route("/news")
def news():
    return render_template("news.html")

"""
WATCHLIST PAGE
"""
@routes.route("/watchlist")
def watchlist():
    return render_template("watchlist.html")

"""
ADMIN PAGE
"""
@routes.route("/admin")
def admin():
    return render_template("admin.html")


@routes.route("/chart")
def chart():
    holdings = [
        {"ticker": "NVDA", "sector": "Technology", "value": 8295},
        {"ticker": "AAPL", "sector": "Technology", "value": 6840},
        {"ticker": "TSLA", "sector": "Consumer",   "value": 5362},
        {"ticker": "MSFT", "sector": "Technology", "value": 3884},
    ]
    return render_template("chart.html", holdings=holdings)
