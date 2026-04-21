import os
import smtplib
import csv
import re
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Load configuration from .env
load_dotenv()

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Fallback to the one seen in seed_demo_students.py if not in env
    DATABASE_URL = "postgresql+psycopg://postgres:postgres@127.0.0.1:15432/verifai"

# SMTP Configuration
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Sending Settings
DELAY_BETWEEN_EMAILS = 2  # Seconds to wait between sends to avoid spam flags

def validate_email(email: str) -> bool:
    """Validates email format using regex."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def load_emails(file_path: str = "recipients.csv") -> list:
    """Loads email addresses from a CSV file."""
    emails = []
    if os.path.exists(file_path):
        try:
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    if row:
                        emails.append(row[0].strip())
        except Exception as e:
            print(f"[!] Error reading CSV: {e}")
    return emails

def load_recipients_from_db() -> list:
    """Fetches all students and their email options from the database."""
    recipients = []
    try:
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        with Session() as session:
            result = session.execute(text("SELECT name, test_email, real_email, preferred_email_type FROM students"))
            for row in result:
                recipients.append({
                    "name": row[0],
                    "test_email": row[1],
                    "real_email": row[2],
                    "preferred_type": row[3]
                })
            print(f"[+] Successfully fetched {len(recipients)} candidates from database.")
    except Exception as e:
        print(f"[!] Database Error: {e}")
    return recipients

def send_email(server, recipient_email: str, name: str) -> str:
    """Sends a single email and returns the status."""
    try:
        subject = f"Hello {name} from VerifAI"
        body = (
            f"Hi {name},\n\n"
            f"You have been shortlisted for the VIZ AI internship opportunity.\n\n"
            f"Please log in to VerifAI portal for next steps.\n\n"
            f"Regards,\n"
            f"VerifAI Team"
        )
        
        msg = MIMEMultipart()
        msg['From'] = GMAIL_USER
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server.send_message(msg)
        return "SUCCESS"
    except smtplib.SMTPRecipientsRefused:
        return "REJECTED"
    except Exception as e:
        print(f"    [!] SMTP Error for {recipient_email}: {e}")
        return "FAILED"

def send_bulk_emails(recipients: list):
    """Orchestrates the bulk sending process with tracking and priority logic."""
    stats = {
        "total": len(recipients),
        "real_sent": 0,
        "test_sent": 0,
        "skipped": 0,
        "failed": 0,
        "invalid": 0,
        "network_errors": 0
    }
    
    if not recipients:
        print("[!] No recipients found to send.")
        return stats

    print(f"[*] Starting bulk send to {len(recipients)} candidates...")
    
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            
            for i, user in enumerate(recipients, 1):
                # Recipient Selection Rule:
                recipient_email = None
                email_type = None
                
                if user["preferred_type"] == "test":
                    recipient_email = user["test_email"]
                    email_type = "TEST"
                else:
                    recipient_email = user["real_email"] or user["test_email"]
                    email_type = "REAL" if user["real_email"] else "TEST"
                
                if not recipient_email or not validate_email(recipient_email):
                    # Fallback to test if real was chosen but empty
                    if not recipient_email and user["test_email"]:
                        recipient_email = user["test_email"]
                        email_type = "TEST"
                    
                    if not recipient_email or not validate_email(recipient_email):
                        print(f"    [{i}] Skipping {user['name']} (No valid email)")
                        stats["skipped"] += 1
                        continue
                
                if not recipient_email:
                    print(f"    [{i}] Skipping {user['name']} (No valid email)")
                    stats["skipped"] += 1
                    continue
                
                print(f"    [{i}] Sending {user['name']} -> {recipient_email} ({email_type})")
                
                status = send_email(server, recipient_email, user["name"])
                
                if status == "SUCCESS":
                    if email_type == "REAL":
                        stats["real_sent"] += 1
                    else:
                        stats["test_sent"] += 1
                else:
                    stats["failed"] += 1
                
                if i < len(recipients):
                    time.sleep(DELAY_BETWEEN_EMAILS)
                    
    except smtplib.SMTPAuthenticationError:
        print("[-] Authentication Failed. Check GMAIL_USER and GMAIL_APP_PASSWORD.")
        stats["network_errors"] += 1
    except Exception as e:
        print(f"[-] Critical Network/SMTP Error: {e}")
        stats["network_errors"] += 1

    return stats

def generate_report(stats: dict):
    """Prints the final execution report."""
    print("\n" + "="*40)
    print("      GMAIL BULK SEND REPORT")
    print("="*40)
    print(f"Total Users:      {stats['total']}")
    print(f"Real Emails Sent: {stats['real_sent']}")
    print(f"Test Emails Sent: {stats['test_sent']}")
    print(f"Skipped:          {stats['skipped']}")
    print(f"Failed:           {stats['failed']}")
    print(f"Status:           {'Completed' if stats['network_errors'] == 0 else 'Completed with Errors'}")
    print("="*40)

if __name__ == "__main__":
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        print("[!] Error: GMAIL credentials not found in .env")
    else:
        candidates = load_recipients_from_db()
        
        if not candidates:
            print("[*] No candidates found in DB. Using demo list...")
            candidates = [
                {"name": "Demo User 1", "real_email": "test1@gmail.com", "test_email": "test1@verifai.dev", "preferred_type": "real"},
                {"name": "Demo User 2", "real_email": None, "test_email": "test2@verifai.dev", "preferred_type": "test"}
            ]
        
        report_stats = send_bulk_emails(candidates[:100])
        generate_report(report_stats)
