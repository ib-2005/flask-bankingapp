from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To
from flask import current_app, render_template
import secrets

def password_email(to_email, recovery_code):

    message = Mail(
        from_email=Email(current_app.config["MAIL_DEFAULT_SENDER"]),
        to_emails=To(to_email),
        subject="Your Password Recovery Code",
        html_content= render_template('auth/email_template.html', recovery_code=recovery_code)
    )

    sg = SendGridAPIClient(current_app.config["SENDGRID_API_KEY"])
    sg.send(message)

def generate_recovery_code():
    return f"{secrets.randbelow(1_000_000):06}"