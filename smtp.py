import os
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("EMAIL_USER"),
    MAIL_PASSWORD= os.getenv("EMAIL_PASS"),
    MAIL_FROM="vitcartracker@mail.oxlac.com",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.mailgun.org",
    MAIL_STARTTLS=True,  # Use STARTTLS for encryption
    MAIL_SSL_TLS=False,  # Do not use SSL/TLS if using STARTTLS
    USE_CREDENTIALS=True
)

async def send_verification_email(email: EmailStr, token: str):
    message = MessageSchema(
        subject="Verify your email",
        recipients=[email],
        body=f"Use the following token to verify your account: {token}",
        subtype="plain"
    )
    fm = FastMail(conf)
    await fm.send_message(message)
