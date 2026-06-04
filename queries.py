
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
