import smtplib
from email.mime.text import MIMEText
import streamlit as st


app_password = st.secrets["APP_PASSWORD"]


def send_reset_email(to_email, temp_password):
    from_email = "roscoadams9@gmail.com"
    app_password = app_password  # Use an App Password from Google

    subject = "Your OnlyFans AI Assistant - Password Reset"
    body = f"Hi there!\n\nYour temporary password is: {temp_password}\n\nPlease log in and change it immediately."

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(from_email, app_password)
            server.send_message(msg)
        return True
    except Exception as e:
        print("Email sending error:", e)
        return False
