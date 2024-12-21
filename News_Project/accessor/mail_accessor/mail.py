import smtplib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import uvicorn


# FastAPI app
app = FastAPI()

class EmailService:
    def __init__(self, smtp_server='smtp.gmail.com', smtp_port=587):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.connection = None

    def connect(self, sender_email, sender_password):
        try:
            self.connection = smtplib.SMTP(self.smtp_server, self.smtp_port)
            self.connection.ehlo()
            self.connection.starttls()
            self.connection.login(sender_email, sender_password)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error connecting to the server: {e}")

    def send_email(self, sender_email, recipient_email, subject, body):
        if not self.connection:
            raise HTTPException(status_code=400, detail="Not connected to the SMTP server.")

        try:
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            self.connection.sendmail(sender_email, recipient_email, msg.as_string())
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to send email: {e}")

    def close_connection(self):
        if self.connection:
            self.connection.close()

# Pydantic model for email details
class EmailRequest(BaseModel):
    recipient_email: str
    subject: str
    body: str

# Endpoint to send an email
@app.post("/send-email/")
async def send_email(email_request: EmailRequest):
    email_service = EmailService()
    email_sender = "put you email"

    email_password = "put you password"
    # Connect to SMTP server
    email_service.connect(email_sender, email_password)

    # Send the email
    email_service.send_email(
        email_sender,
        email_request.recipient_email,
        email_request.subject,
        email_request.body
    )

    # Close the connection
    email_service.close_connection()

    return {"message": "Email sent successfully"}

# Add this block to run the app directly with uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8003)
