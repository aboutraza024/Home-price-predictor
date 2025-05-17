import os
import asyncio
from fastapi import HTTPException
from fastapi.responses import JSONResponse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
load_dotenv()

auth_email = os.getenv("email")
password = os.getenv("password")
# print(email, password)

fixed_subject = "Verification Code"


# Function to send email
async def send_verification_code(user_email,verification_code):
    fixed_message = f"Your 6 digit Verification code: {verification_code}"
    smtp_server = "smtp.gmail.com"
    smtp_port = 587  # TLS port for Gmail
    msg = MIMEMultipart()
    msg["From"] = auth_email  # Replace with your email
    msg["To"] = user_email
    msg["Subject"] = fixed_subject
    msg.attach(MIMEText(fixed_message, "plain"))
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Upgrade connection to TLS
            server.login(auth_email, password)  # Login with your email credentials
            server.sendmail(auth_email, user_email, msg.as_string())  # Send email
            return JSONResponse(
                status_code=200, content={"details": f"Email sent successfully to {user_email}"}
            )

    except Exception as e:
        print(f"Error sending email: {e}")
        raise HTTPException(status_code=500, detail="Email not sent successfully")
#
# async def main():
#     await send_email1("razamehar024@gmail.com", "1209345")
#
# if __name__ == "__main__":
#     asyncio.run(main())
