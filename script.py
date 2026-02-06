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
        
        now_pak = datetime.utcnow() + timedelta(hours=5)
        current_hour = now_pak.hour
        today_dates = [now_pak.strftime("%d %B"), now_pak.strftime("%-d %B")]
        two_days_dates = [(now_pak + timedelta(days=2)).strftime("%d %B"), 
                          (now_pak + timedelta(days=2)).strftime("%-d %B")]

        print(f"PK Time: {now_pak.strftime('%H:%M')}")
        print(f"Targeting Dates: {two_days_dates}")

        try:
            page.goto("https://lms.superior.edu.pk/login/index.php", wait_until="networkidle")
            page.fill('input[name="username"]', LMS_USER)
            page.fill('input[name="password"]', LMS_PASS)
            page.keyboard.press("Enter")
            
            # 15 seconds wait taaki Dashboard aur Timeline load ho jaye
            print("Waiting for Dashboard...")
            page.wait_for_timeout(15000) 

            # Har wo cheez uthao jo event ho sakti hai
            all_events = page.query_selector_all('.event-name, .timeline-event-list-item, [data-region="event-list-item"]')
            print(f"Total items found on page: {len(all_events)}")

            urgent_tasks = []
            upcoming_tasks = []
            
            for item in all_events:
                try:
                    text = item.inner_text().strip()
                    # Agar item ke andar hi date hai to date_text wahi hoga
                    date_text = text 
                    
                    # Behtar detection ke liye pura text check karein
                    if any(d in date_text for d in ["Today", "today"]) or any(d in date_text for d in today_dates):
                        if text not in urgent_tasks: urgent_tasks.append(text)
                    elif any(d in date_text for d in two_days_dates):
                        if text not in upcoming_tasks: upcoming_tasks.append(text)
                except:
                    continue

            # --- NOTIFICATION LOGIC ---
            if 9 <= current_hour <= 11:
                if not urgent_tasks and not upcoming_tasks:
                    send_email("LMS Update: No tasks today ✅", "Asalam-o-Alaikum! Aaj ke liye koi pending task nahi mila.")
                elif urgent_tasks:
                    send_email("LMS URGENT: Due TODAY! ⚠️", "\n\n".join(urgent_tasks))

            elif 16 <= current_hour <= 18:
                if urgent_tasks:
                    send_email("LMS Evening Alert: Due TODAY! ⚠️", "\n\n".join(urgent_tasks))
                elif upcoming_tasks:
                    send_email("LMS Alert: 2 Days Left! ⏳", "Ye tasks 2 din baad due hain:\n\n" + "\n\n".join(upcoming_tasks))
                else:
                    # Debugging ke liye: Agar 5 baje koi task nahi mila
                    print("No matching tasks for the 2-day rule.")

            elif current_hour >= 21:
                if urgent_tasks:
                    send_email("LMS FINAL WARNING! 🚨", "\n\n".join(urgent_tasks))

        except Exception as e:
            print(f"Error: {e}")
        browser.close()

if __name__ == "__main__":
    run_bot()
