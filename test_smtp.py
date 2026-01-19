import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

def test_smtp():
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    
    print(f"Testing SMTP connection to {host}:{port}...")
    print(f"User: {user}")
    
    try:
        server = smtplib.SMTP(host, port)
        server.starttls()
        server.login(user, password)
        print("✅ Login successful!")
        
        msg = MIMEText("This is a test email from TrueCheck backend.")
        msg['Subject'] = 'TrueCheck SMTP Test'
        msg['From'] = user
        msg['To'] = user  # Send to self
        
        server.send_message(msg)
        print("✅ Test email sent successfully!")
        server.quit()
    except Exception as e:
        print(f"❌ SMTP Error: {e}")

if __name__ == "__main__":
    test_smtp()
