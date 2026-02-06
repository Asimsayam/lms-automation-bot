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
        
        # Pakistan Time Calculation
        now_pak = datetime.utcnow() + timedelta(hours=5)
        current_hour = now_pak.hour
        
        # Multiple date formats to match LMS (e.g. "8 February" and "08 February")
        today_dates = [now_pak.strftime("%d %B"), now_pak.strftime("%-d %B")]
        two_days_dates = [(now_pak + timedelta(days=2)).strftime("%d %B"), 
                          (now_pak + timedelta(days=2)).strftime("%-d %B")]

        print(f"Current PK Time: {now_pak.strftime('%Y-%m-%d %H:%M')}")
        print(f"Looking for dates: Today={today_dates}, In 2 Days={two_days_dates}")

        try:
            page.goto("https://lms.superior.edu.pk/login/index.php", wait_until="networkidle")
            page.fill('input[name="username"]', LMS_USER)
            page.fill('input[name="password"]', LMS_PASS)
            page.keyboard.press("Enter")
            page.wait_for_timeout(10000) # Give it 10 seconds to fully load dashboard

            tasks_found = page.query_selector_all('.timeline-event-list-item')
            urgent_tasks = []
            upcoming_tasks = []
            
            for item in tasks_found:
                try:
                    name = item.query_selector('.event-name').inner_text().strip()
                    date_text = item.query_selector('.small.text-muted').inner_text().strip()
                    
                    course_info = "N/A"
                    course_el = item.query_selector('.text-muted') or item.query_selector('a[href*="course/view.php"]')
                    if course_el:
                        course_info = course_el.inner_text().split('|')[0].strip()
                    
                    full_info = f"📌 {name}\n   📖 Subject: {course_info}\n   ⏰ Deadline: {date_text}"
                    
                    # Logic to match dates
                    if any(d in date_text for d in ["Today", "today"]) or any(d in date_text for d in today_dates):
                        urgent_tasks.append(full_info)
                    elif any(d in date_text for d in two_days_dates):
                        upcoming_tasks.append(full_info)
                except:
                    continue

            # --- SMART RULES ---
            # 1. Subah 10 baje (9 to 11 AM) - Report hamesha bhejni hai
            if 9 <= current_hour <= 11:
                if not urgent_tasks and not upcoming_tasks:
                    send_email("LMS Update: No tasks today ✅", "Asalam-o-Alaikum! Aaj ke liye koi pending task nahi mila.")
                elif urgent_tasks:
                    send_email("LMS URGENT: Tasks due TODAY! ⚠️", "Ye tasks AAJ submit karne hain:\n\n" + "\n\n".join(urgent_tasks))

            # 2. Shaam 5 baje (4 to 6 PM) - 2 din pehle ka alert
            elif 16 <= current_hour <= 18:
                if urgent_tasks:
                    send_email("LMS Evening Reminder: Tasks due TODAY! ⚠️", "Friendly reminder, ye tasks AAJ khatam ho rahe hain:\n\n" + "\n\n".join(urgent_tasks))
                elif upcoming_tasks:
                    send_email("LMS Alert: 2 Days Left! ⏳", "Asalam-o-Alaikum! Ye tasks 2 din baad due hain:\n\n" + "\n\n".join(upcoming_tasks))

            # 3. Raat 11 baje (9 to 12 PM) - Final Warning
            elif current_hour >= 21:
                if urgent_tasks:
                    send_email("LMS FINAL WARNING: Submit Now! 🚨", "Ye tasks AAJ ki date mein hain, foran upload karein:\n\n" + "\n\n".join(urgent_tasks))

        except Exception as e:
            print(f"Error: {e}")
        browser.close()

if __name__ == "__main__":
    run_bot()
