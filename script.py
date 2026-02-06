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
        # Browser launch karein (window size barha di hai debugging ke liye)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = context.new_page()
        
        try:
            print("Opening Superior LMS...")
            page.goto("https://lms.superior.edu.pk/login/index.php", wait_until="networkidle", timeout=60000)
            
            print("Entering credentials...")
            page.wait_for_selector('input[name="username"]', timeout=30000)
            page.fill('input[name="username"]', LMS_USER)
            page.fill('input[name="password"]', LMS_PASS)
            
            print("Attempting to click Login button...")
            # Ye 3 alag tareeqon se button dhoondega
            login_selectors = [
                'button#loginbtn', 
                'input#loginbtn', 
                'button:has-text("Log in")', 
                '.btn-primary'
            ]
            
            clicked = False
            for selector in login_selectors:
                if page.is_visible(selector):
                    page.click(selector)
                    print(f"Clicked using: {selector}")
                    clicked = True
                    break
            
            if not clicked:
                print("Could not find login button with standard selectors. Pressing Enter instead...")
                page.keyboard.press("Enter")

            # Dashboard ka intezar
            print("Waiting for Dashboard...")
            page.wait_for_timeout(5000) # 5 second ruko taaki page load ho jaye
            
            # Check success
            if "Dashboard" in page.content() or "My courses" in page.content() or "Logout" in page.content():
                print("SUCCESS: Logged in to Superior LMS!")
                send_email("LMS Bot Alert", "Superior LMS Login Successful! Bot is now active.")
            else:
                print("Current Page Title:", page.title())
                print("Login might have failed or took too long.")
                
        except Exception as e:
            print(f"An error occurred: {e}")
            
        browser.close()

if __name__ == "__main__":
    run_bot()
