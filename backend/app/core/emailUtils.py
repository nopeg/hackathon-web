import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from jose import jwt
from app.core.config import settingsInstance

def generateVerificationToken(email: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=24)
    payload = {"sub": email, "exp": expire, "type": "verification"}
    return jwt.encode(payload, settingsInstance.secretKey, algorithm=settingsInstance.algorithm)

def sendVerificationEmail(emailTo: str, token: str, baseUrl: str):
    if not settingsInstance.smtpHost or not settingsInstance.smtpUser:
        print(f"SMTP not configured. Would send email to {emailTo} with token {token}")
        return
    verificationUrl = f"{baseUrl}/auth/verifyEmail?token={token}"
    subject = "Подтверждение регистрации"
    body = f"Для подтверждения email перейдите по ссылке: {verificationUrl}\nСсылка действительна 24 часа."
    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = settingsInstance.smtpUser
    msg["To"] = emailTo
    with smtplib.SMTP_SSL(settingsInstance.smtpHost, settingsInstance.smtpPort) as server:
        server.login(settingsInstance.smtpUser, settingsInstance.smtpPassword)
        server.send_message(msg)