import secrets
from flask import Blueprint, request, render_template, redirect, session
from queries import create_user, get_user_by_email
from db import get_connection, DB_NAME
from werkzeug.security import generate_password_hash, check_password_hash
from mail import send_verification_email

routes = Blueprint("routes", __name__)


@routes.route("/")
def home():
    return {"message": "Flask API running"}

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
    
    print("user logged in")

    return redirect("/home")
    
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

    return redirect("/login")
    
"""
HANDLES EMAIL VERIFICATION
"""
@routes.route("/verify/<token>")
def verify_token(token):
    conn = get_connection("portfolio_database")

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
