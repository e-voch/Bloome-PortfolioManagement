from flask import Flask
from routes import routes
from mail import mail
from datetime import timedelta
from auth import init_jwt

app = Flask(__name__)

app.secret_key = "secret-key"
app.register_blueprint(routes)

app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=30)
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_COOKIE_SAMESITE"] = "Lax"
app.config["JWT_ACCESS_COOKIE_PATH"] = "/"
app.config["JWT_COOKIE_SECURE"] = False
app.config["JWT_COOKIE_CSRF_PROTECT"] = False

app.config.update(
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME="bloome.notifications@gmail.com",
    MAIL_PASSWORD="nuqb mqoo vvxg defb",
    MAIL_DEFAULT_SENDER="bloome.notifications@gmail.com"
)

mail.init_app(app)
init_jwt(app)

if __name__ == "__main__":
    app.run(debug=True)
