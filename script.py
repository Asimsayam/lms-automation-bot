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
        
        # Pakistan Time (UTC + 5)
        now_pakistan = datetime.utcnow() + timedelta(hours=5)
        current_hour = now_pakistan.hour
        today_str = now_pakistan.strftime("%d %B")
        two_days_later = (now_pakistan + timedelta(days=2)).strftime("%d %B")

        try:
            print("Opening LMS...")
            page.goto("https://lms.superior.edu.pk/login/index.php", wait_until="networkidle")
            page.fill('input[name="username"]', LMS_USER)
            page.fill('input[name="password"]', LMS_PASS)
            page.keyboard.press("Enter")
            page.wait_for_timeout(8000)

            print("Checking Timeline for Tasks & Subjects...")
            tasks = page.query_selector_all('.timeline-event-list-item')
            urgent_tasks = []
            upcoming_tasks = []
            
            for item in tasks:
                try:
                    # Task ka naam (e.g. Assignment 1)
                    name = item.query_selector('.event-name').inner_text().strip()
                    
                    # Subject/Course ka naam dhoondna
                    # Moodle mein ye aksar 'small' text ya link mein hota hai
                    course_info = ""
                    course_el = item.query_selector('.text-muted') or item.query_selector('a[href*="course/view.php"]')
                    if course_el:
                        course_info = course_el.inner_text().split('|')[0].strip() # Clean course name
                    
                    # Deadline ki tareekh
                    date_text = item.query_selector('.small.text-muted').inner_text().strip()
                    
                    full_info = f"📌 {name}\n   📖 Subject: {course_info}\n   ⏰ Deadline: {date_text}"
                    
                    if "Today" in date_text or today_str in date_text:
                        urgent_tasks.append(full_info)
                    elif two_days_later in date_text:
                        upcoming_tasks.append(full_info)
                except:
                    continue

            # --- RULES ---
            if not urgent_tasks and not upcoming_tasks:
                if current_hour == 10:
                    send_email("LMS Update: No tasks today ✅", "Asalam-o-Alaikum! Aaj ke liye koi pending task nahi mila. Relax!")
            
            if urgent_tasks:
                time_msg = "URGENT - LAST CHANCE!" if current_hour >= 22 else "Daily Reminder"
                body = f"Asalam-o-Alaikum,\n\nYe tasks AAJ submit karne hain:\n\n" + "\n\n".join(urgent_tasks)
                send_email(f"LMS Alert: {time_msg}", body)

            elif upcoming_tasks and current_hour == 17:
                body = f"Asalam-o-Alaikum,\n\nYe tasks 2 DIN BAAD due hain. Inhain waqt par mukammal karlein:\n\n" + "\n\n".join(upcoming_tasks)
                send_email("LMS Alert: 2 Days Left! ⏳", body)

        except Exception as e:
            print(f"Error: {e}")
        browser.close()

if __name__ == "__main__":
    run_bot()
