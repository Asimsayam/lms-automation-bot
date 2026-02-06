import os
import smtplib
from playwright.sync_api import sync_playwright
from email.message import EmailMessage
from datetime import datetime, timedelta

# Credentials
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
        print(f"Email sent: {subject}")
    except Exception as e:
        print(f"Error sending email: {e}")

def run_bot():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        now_pak = datetime.utcnow() + timedelta(hours=5)
        current_hour = now_pak.hour
        
        # Target Dates (e.g., "8 February" and "08 February")
        today = [now_pak.strftime("%d %B"), now_pak.strftime("%-d %B")]
        two_days = [(now_pak + timedelta(days=2)).strftime("%d %B"), 
                    (now_pak + timedelta(days=2)).strftime("%-d %B")]

        try:
            print(f"Logging into Superior LMS at {now_pak.strftime('%H:%M')}...")
            page.goto("https://lms.superior.edu.pk/login/index.php", wait_until="networkidle")
            page.fill('input[name="username"]', LMS_USER)
            page.fill('input[name="password"]', LMS_PASS)
            page.keyboard.press("Enter")
            
            # Dashboard load hone ka wait
            page.wait_for_timeout(15000)
            
            # PURE PAGE KA TEXT UTHALO (Sabse asaan aur pakka tareeka)
            page_text = page.content()
            
            urgent_found = any(d in page_text for d in ["Today", "today"] + today)
            upcoming_found = any(d in page_text for d in two_days)

            # --- FINAL RULES ---
            # 1. Subah ka time (9-11 AM)
            if 9 <= current_hour <= 11:
                if urgent_found:
                    send_email("LMS URGENT: Due TODAY! ⚠️", "Aapka koi task aaj khatam ho raha hai. Please LMS check karein.")
                elif upcoming_found:
                    send_email("LMS Alert: 2 Days Left! ⏳", "Aapka koi task 2 din baad due hai. Check karlein.")
                else:
                    send_email("LMS Update: No tasks today ✅", "Aaj ke liye koi pending task nahi mila.")

            # 2. Shaam ka time (4-6 PM)
            elif 16 <= current_hour <= 18:
                if urgent_found:
                    send_email("LMS Evening Alert: Due TODAY! ⚠️", "Reminder: Aaj ki deadline wala task rehta hai.")
                elif upcoming_found:
                    send_email("LMS Alert: 2 Days Left! ⏳", "Reminder: 2 din baad ki deadline wala task pending hai.")
                else:
                    print("No tasks found for evening alert.")

            # 3. Raat ka time (9-12 PM)
            elif current_hour >= 21:
                if urgent_found:
                    send_email("LMS FINAL WARNING! 🚨", "Deadline khatam hone wali hai, task upload kar dein!")

        except Exception as e:
            print(f"Error occurred: {e}")
        
        browser.close()

if __name__ == "__main__":
    run_bot()
