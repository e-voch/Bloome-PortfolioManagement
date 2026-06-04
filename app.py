from flask import Flask
from routes import routes
from mail import mail

app = Flask(__name__)

app.secret_key = "secret-key"
app.register_blueprint(routes)

app.config.update(
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME="bloome.notifications@gmail.com",
    MAIL_PASSWORD="nuqb mqoo vvxg defb",
    MAIL_DEFAULT_SENDER="bloome.notifications@gmail.com"
)

mail.init_app(app)

if __name__ == "__main__":
    app.run(debug=True)
