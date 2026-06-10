import secrets
import csv
import io
from flask import Blueprint, request, render_template, redirect, session, flash, get_flashed_messages, make_response, url_for
from queries import create_user, get_user_by_email, get_total_value, get_daily_gain, get_original_investment, get_holdings, get_transactions
from queries import create_transaction, get_stock_from_ticker, get_news_for_stock_id, update_user_name, update_user_email, set_verification_token, update_user_password, delete_user
from queries import get_watchlist, get_all_stocks, add_to_watchlist, remove_from_watchlist
from db import get_connection, DB_NAME
from werkzeug.security import generate_password_hash, check_password_hash
from mail import send_verification_email
from helper import generate_stock_allocation_values, generate_industry_allocation_values

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
    email = request.form["email"]
    password = request.form["password"]
    
    conn = get_connection(DB_NAME)
    cursor = conn.cursor(dictionary=True)

    user = get_user_by_email(cursor, email) 
    
    if not user or not check_password_hash(user["password"], password):
        flash("Incorrect email or password", "danger")
        return redirect("/login")
    
    if not user["is_verified"]:
        flash("Please verify your email first", "danger")
        return redirect("/login")

    session["user_id"] = user["id"]
    session["name"] = user["name"]
    
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
        flash("A user with that email already exists", "danger")
        cursor.close()
        conn.close()

        return redirect("/signup")

    create_user(cursor, name, email, hashed_password, token)

    conn.commit()

    cursor.close()
    conn.close()

    send_verification_email(email, token)

    flash("Account created! Please verify your email", 'success')

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
    chart_colours = ['#4285f4', '#34a853', '#f4511e', '#888']
    conn = get_connection(DB_NAME)

    cursor = conn.cursor()

    total_value = get_total_value(cursor, session.get("user_id"))
    day_change = get_daily_gain(cursor, session.get("user_id")) 
    total_investment = get_original_investment(cursor, session.get("user_id")) 

    total_gain = total_value - total_investment
    day_change_percentage = round((day_change / total_value) * 100) if total_value else 0
    total_return_percentage = round((total_gain / total_investment) * 100) if total_investment else 0

    holdings = get_holdings(cursor, session.get("user_id"))
    
    stock_allocation_chart_values = generate_stock_allocation_values(holdings, total_value, chart_colours) 
    industry_allocation_chart_values =  generate_industry_allocation_values(holdings, total_value, chart_colours) 

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
         total_return_percentage=total_return_percentage,
         stock_allocation_chart_values=stock_allocation_chart_values,
         industry_allocation_chart_values=industry_allocation_chart_values,
         chart_colours=chart_colours
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

    holdings = [list(row[:-1]) + [round((row[4] / total_value) * 100, 2)] for row in data] 

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

    transactions.sort(key=lambda x: x[0], reverse=True)
    
    open_modal = request.args.get("open_modal") == "1"
    
    conn.commit()
    cursor.close()
    conn.close()

    return render_template(
        "transactions.html",
        transactions = transactions,
        name = session.get("name"),
        open_modal=open_modal
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
    stock_details = get_stock_from_ticker(cursor, ticker.upper())
        
    print(stock_details)

    if not stock_details:
        flash("Stock ticker not recognised", "danger")
        return redirect("/transactions?open_modal=1")
    
    stock_id = stock_details['id']

    create_transaction(cursor, user_id, stock_id, side, shares, price, date)
    recompute_holding(cursor, user_id, stock_id)

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/transactions")


"""
DELETES TRANSACTION
"""
@routes.route("/delete_transaction/<int:transaction_id>", methods = ["POST"])
def remove_transaction(transaction_id):
    conn = get_connection(DB_NAME)
    cursor = conn.cursor(dictionary=True)
    
    transaction_details = get_transaction(cursor, transaction_id) 

    delete_transaction(cursor, transaction_id)
    recompute_holding(cursor, session["user_id"], transaction_details['stock_id'])
    
    conn.commit()
    conn.close()

    return redirect("/transactions")

"""
NEWS PAGE
"""
@routes.route("/news")
def news():
    conn = get_connection(DB_NAME)
    cursor = conn.cursor(dictionary=True)

    user_id = session.get("user_id")

    holdings = get_holdings(cursor, user_id)
    
    stock_ids = [h['stock_id'] for h in holdings]
        
    articles = []

    for s_id in stock_ids:
        articles.extend(get_news_for_stock_id(cursor, s_id))

    return render_template(
        "news.html",
        name = session["name"],
        articles=articles
    )

"""
WATCHLIST PAGE
"""
@routes.route("/watchlist")
def watchlist():
    user_id = session.get("user_id")
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()

    watchlist_items = get_watchlist(cursor, user_id)
    all_stocks = get_all_stocks(cursor)

    cursor.close()
    conn.close()

    watchlist_ids = [row[0] for row in watchlist_items]

    all_stocks_json = [
        (row[0], row[1], row[2],
         float(row[3]) if row[3] is not None else None,
         float(row[4]) if row[4] is not None else None,
         float(row[5]) if row[5] is not None else None)
        for row in all_stocks
    ]

    return render_template(
        "watchlist.html",
        name=session.get("name"),
        watchlist=watchlist_items,
        all_stocks=all_stocks_json,
        watchlist_ids=watchlist_ids
    )


"""
WATCHLIST - ADD
"""
@routes.route("/watchlist/add", methods=["POST"])
def watchlist_add():
    user_id = session.get("user_id")
    stock_id = request.form.get("stock_id")
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    add_to_watchlist(cursor, user_id, stock_id)
    conn.commit()
    cursor.close()
    conn.close()
    return redirect("/watchlist")


"""
WATCHLIST - REMOVE
"""
@routes.route("/watchlist/remove", methods=["POST"])
def watchlist_remove():
    user_id = session.get("user_id")
    stock_id = request.form.get("stock_id")
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    remove_from_watchlist(cursor, user_id, stock_id)
    conn.commit()
    cursor.close()
    conn.close()
    return redirect("/watchlist")

"""
ADMIN PAGE
"""
@routes.route("/admin")
def admin():
    conn = get_connection(DB_NAME)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT name, email, is_verified FROM users WHERE id = %s", (session.get("user_id"),))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    messages = {cat: msg for cat, msg in get_flashed_messages(with_categories=True)}

    return render_template(
        "admin.html",
        name=user["name"] if user else "",
        email=user["email"] if user else "",
        is_verified=user["is_verified"] if user else False,
        edit=request.args.get("edit"),
        messages=messages
    )


"""
ADMIN - UPDATE NAME
"""
@routes.route("/admin/update-name", methods=["POST"])
def admin_update_name():
    new_name = request.form.get("name", "").strip()

    if not new_name:
        flash("Name cannot be empty.", "name_error")
        return redirect("/admin?edit=name")

    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    update_user_name(cursor, session.get("user_id"), new_name)
    conn.commit()
    cursor.close()
    conn.close()

    session["name"] = new_name
    flash("Name updated successfully.", "name_success")
    return redirect("/admin")


"""
ADMIN - UPDATE EMAIL
Sets is_verified to False so the user must re-verify their new email.
"""
@routes.route("/admin/update-email", methods=["POST"])
def admin_update_email():
    user_id = session.get("user_id")
    new_email = request.form.get("email", "").strip()

    if not new_email:
        flash("Email cannot be empty.", "email_error")
        return redirect("/admin?edit=email")

    conn = get_connection(DB_NAME)
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id FROM users WHERE email = %s AND id != %s", (new_email, user_id))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        flash("That email is already in use.", "email_error")
        return redirect("/admin?edit=email")

    update_user_email(cursor, user_id, new_email)
    conn.commit()
    cursor.close()
    conn.close()

    flash("Email updated. Please verify your new email address.", "email_success")
    return redirect("/admin")


"""
ADMIN - SEND VERIFICATION EMAIL
Generates a fresh token and sends the verification email to the user's current email.
"""
@routes.route("/admin/send-verification", methods=["POST"])
def admin_send_verification():
    user_id = session.get("user_id")
    token = secrets.token_urlsafe(32)

    conn = get_connection(DB_NAME)
    cursor = conn.cursor(dictionary=True)
    set_verification_token(cursor, user_id, token)
    conn.commit()

    cursor.execute("SELECT email FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    send_verification_email(user["email"], token)
    flash("Verification email sent! Check your inbox.", "verified_success")
    return redirect("/admin")


"""
ADMIN - UPDATE PASSWORD
"""
@routes.route("/admin/update-password", methods=["POST"])
def admin_update_password():
    user_id = session.get("user_id")
    current_password = request.form.get("current_password", "")
    new_password  = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not new_password:
        flash("New password cannot be empty.", "password_error")
        return redirect("/admin?edit=password")

    if new_password != confirm_password:
        flash("Passwords do not match.", "password_error")
        return redirect("/admin?edit=password")

    conn = get_connection(DB_NAME)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT password FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    if not user or not check_password_hash(user["password"], current_password):
        cursor.close()
        conn.close()
        flash("Current password is incorrect.", "password_error")
        return redirect("/admin?edit=password")

    update_user_password(cursor, user_id, generate_password_hash(new_password))
    conn.commit()
    cursor.close()
    conn.close()

    flash("Password updated successfully.", "password_success")
    return redirect("/admin")


"""
ADMIN - EXPORT DATA AS CSV
"""
@routes.route("/admin/export")
def admin_export():
    user_id = session.get("user_id")
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()

    holdings = get_holdings(cursor, user_id)
    transactions = get_transactions(cursor, user_id)

    cursor.close()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Holdings"])
    writer.writerow(["Symbol", "Quantity", "Avg Cost", "Current Price", "Value", "Gain/Loss"])
    for row in holdings:
        writer.writerow(row[:6])

    writer.writerow([])

    writer.writerow(["Transactions"])
    writer.writerow(["Date", "Symbol", "Type", "Quantity", "Price", "Total"])
    for row in transactions:
        writer.writerow(row)

    output.seek(0)
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=portfolio_export.csv"
    response.headers["Content-Type"] = "text/csv"
    return response


"""
LOGOUT
"""
@routes.route("/logout")
def logout():
    session.clear()
    return redirect("/")


"""
ADMIN - DELETE ACCOUNT
"""
@routes.route("/admin/delete-account", methods=["POST"])
def admin_delete_account():
    confirm = request.form.get("confirm", "")
    if confirm != "CONFIRM":
        flash("Please type CONFIRM to delete your account.", "delete_error")
        return redirect("/admin")

    user_id = session.get("user_id")
    conn = get_connection(DB_NAME)
    cursor = conn.cursor()
    delete_user(cursor, user_id)
    conn.commit()
    cursor.close()
    conn.close()

    session.clear()
    return redirect("/")


@routes.route("/chart")
def chart():
    holdings = [
        {"ticker": "NVDA", "sector": "Technology", "value": 8295},
        {"ticker": "AAPL", "sector": "Technology", "value": 6840},
        {"ticker": "TSLA", "sector": "Consumer",   "value": 5362},
        {"ticker": "MSFT", "sector": "Technology", "value": 3884},
    ]
    return render_template("chart.html", holdings=holdings)

"""
STOCK PAGE
"""
@routes.route("/stocks/<ticker>")
def stock_detail(ticker):
    return render_template("stocks.html", ticker=ticker)
