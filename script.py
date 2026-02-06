import os
import smtplib
from playwright.sync_api import sync_playwright
from email.message import EmailMessage
from datetime import datetime, timedelta

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
        context = browser.new_context()
        page = context.new_page()
        
        # Pakistan Time nikalne ke liye (UTC + 5)
        current_hour = (datetime.utcnow() + timedelta(hours=5)).hour
        today_str = (datetime.utcnow() + timedelta(hours=5)).strftime("%d %B")
        two_days_later = (datetime.utcnow() + timedelta(hours=5, days=2)).strftime("%d %B")

        try:
            page.goto("https://lms.superior.edu.pk/login/index.php", wait_until="networkidle")
            page.fill('input[name="username"]', LMS_USER)
            page.fill('input[name="password"]', LMS_PASS)
            page.keyboard.press("Enter")
            page.wait_for_timeout(7000)

            tasks = page.query_selector_all('.timeline-event-list-item')
            urgent_tasks = [] # Aaj khatam hone wale
            upcoming_tasks = [] # 2 din baad wale
            
            for item in tasks:
                name = item.query_selector('.event-name').inner_text()
                date_text = item.query_selector('.small.text-muted').inner_text()
                full_text = f"{name} ({date_text})"
                
                if "Today" in date_text or today_str in date_text:
                    urgent_tasks.append(full_text)
                elif two_days_later in date_text:
                    upcoming_tasks.append(full_text)

            # --- LOGIC RULES ---
            
            # 1. Agar koi task nahi hai (Sirf Subah 10 baje mail bhejega)
            if not urgent_tasks and not upcoming_tasks:
                if current_hour == 10:
                    send_email("LMS Update: No tasks today", "Asalam-o-Alaikum! Aaj ke liye koi pending task nahi mila. Relax!")
            
            # 2. Agar task aaj khatam ho raha hai (10AM, 5PM, 11PM teeno waqt bhejega)
            if urgent_tasks:
                time_msg = "LAST CHANCE!" if current_hour >= 22 else "Reminder"
                body = f"URGENT: Ye tasks AAJ submit karne hain:\n\n" + "\n".join(urgent_tasks)
                send_email(f"LMS URGENT Alert: {time_msg}", body)

            # 3. Agar task 2 din baad hai (Sirf shaam 5 baje alert bhejega)
            elif upcoming_tasks and current_hour == 17:
                body = f"Reminder: Ye tasks 2 din baad DUE hain. Taiyari karlein:\n\n" + "\n".join(upcoming_tasks)
                send_email("LMS Alert: 2 Days Left!", body)

        except Exception as e:
            print(f"Error: {e}")
        browser.close()

if __name__ == "__main__":
    run_bot()
