import os
import smtplib
from playwright.sync_api import sync_playwright
from email.message import EmailMessage

# Ye values hum GitHub Secrets se uthayenge
LMS_USER = os.environ.get('LMS_USER')
LMS_PASS = os.environ.get('LMS_PASS')
EMAIL_USER = os.environ.get('EMAIL_USER')
EMAIL_PASS = os.environ.get('EMAIL_PASS')

def send_email(subject, body):
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_USER 
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_USER, EMAIL_PASS)
            smtp.send_message(msg)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

def run_bot():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("Logging into LMS...")
        # Yahan aap apne LMS ka sahi URL dalein
        page.goto("https://lms.vcomsats.edu.pk/login.php") 
        
        # Ye niche wale selectors aapko apne LMS ke hisab se badalne honge
        # Filhal ye ek example hai
        try:
            page.fill('input[name="username"]', LMS_USER)
            page.fill('input[name="password"]', LMS_PASS)
            page.click('button[type="submit"]')
            page.wait_for_load_state("networkidle")
            
            print("Successfully logged in! Checking deadlines...")
            # Alert bhejne ka logic
            send_email("LMS Check", "Bot successfully logged in and checked the dashboard.")
            
        except Exception as e:
            print(f"An error occurred: {e}")
            
        browser.close()

if __name__ == "__main__":
    run_bot()
