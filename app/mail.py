from flask_mail import Mail, Message

mail = Mail()

def send_verification_email(email, token):
    msg = Message(
        subject="Verify your email",
        recipients=[email]
    )

    verification_link = f"http://localhost:5000/verify/{token}"

    msg.body = (
        "Thank you for signing up \n\n"
        f"Verify your account here:\n{verification_link}"
    )

    mail.send(msg)
