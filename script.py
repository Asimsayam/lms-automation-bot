import os
import smtplib
from playwright.sync_api import sync_playwright
from email.message import EmailMessage

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
        # Browser launch karein
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            print("Opening Superior LMS...")
            page.goto("https://lms.superior.edu.pk/login/index.php", wait_until="networkidle")
            
            print("Entering credentials...")
            # Superior LMS ke sahi selectors
            page.fill('input#username', LMS_USER)
            page.fill('input#password', LMS_PASS)
            
            print("Clicking login...")
            page.click('button#loginbtn')
            
            # Login hone ka intezar karein
            page.wait_for_load_state("networkidle")
            
            # Check karein login kamyab hua ya nahi
            if "Dashboard" in page.title() or "My courses" in page.content():
                print("Successfully logged in!")
                send_email("LMS Bot Alert", "Bot successfully logged into Superior LMS Dashboard.")
            else:
                print("Login might have failed. Dashboard not found.")
                
        except Exception as e:
            print(f"An error occurred: {e}")
            # Error ki surat mein bhi screenshot le sakte hain debugging ke liye
            page.screenshot(path="error.png")
            
        browser.close()

if __name__ == "__main__":
    run_bot()
