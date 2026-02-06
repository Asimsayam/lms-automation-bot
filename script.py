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
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            print("Opening Superior LMS...")
            # Timeout barha diya hai taaki agar site slow ho to masla na ho
            page.goto("https://lms.superior.edu.pk/login/index.php", wait_until="load", timeout=60000)
            
            print("Waiting for login fields...")
            # Intezar karein jab tak username box nazar na aa jaye
            page.wait_for_selector('#username', timeout=30000)
            
            print("Entering credentials...")
            page.fill('#username', LMS_USER)
            page.fill('#password', LMS_PASS)
            
            print("Clicking login button...")
            # Selector ko simple kar diya hai (#loginbtn)
            page.click('#loginbtn')
            
            # Dashboard aane ka intezar
            print("Waiting for Dashboard to load...")
            page.wait_for_load_state("networkidle")
            
            if "Dashboard" in page.content() or "My courses" in page.content():
                print("Successfully logged in!")
                send_email("LMS Bot Alert", "Superior LMS Login Successful! Bot is working.")
            else:
                print("Login status unclear. Checking content...")
                # Agar login fail hua to ye print hoga
                print("Page Title:", page.title())
                
        except Exception as e:
            print(f"An error occurred: {e}")
            
        browser.close()

if __name__ == "__main__":
    run_bot()
