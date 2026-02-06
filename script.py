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
            page.goto("https://lms.superior.edu.pk/login/index.php", wait_until="networkidle")
            
            print("Logging in...")
            page.fill('input[name="username"]', LMS_USER)
            page.fill('input[name="password"]', LMS_PASS)
            page.keyboard.press("Enter")
            
            # Dashboard load hone ka intezar
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(5000) # Thoda extra time loading ke liye

            print("Checking for Tasks/Assignments...")
            # Moodle LMS mein 'Timeline' section ko dhoondna
            tasks_found = []
            
            # Timeline mein jo events hote hain unke selectors
            event_selectors = [
                '.event-name', 
                '.list-group-item[data-region="event-list-item"]',
                '.timeline-event-list-item'
            ]
            
            for selector in event_selectors:
                elements = page.query_selector_all(selector)
                for el in elements:
                    text = el.inner_text().strip()
                    if text and text not in tasks_found:
                        tasks_found.append(text)

            if tasks_found:
                print(f"Found {len(tasks_found)} tasks!")
                task_list = "\n".join([f"- {task}" for task in tasks_found])
                email_body = f"Hello! Following tasks were found on your Superior LMS:\n\n{task_list}\n\nCheck here: https://lms.superior.edu.pk/my/"
                send_email("LMS Task Alert! 📢", email_body)
            else:
                print("No pending tasks found.")
                # Agar aap chahte hain ke task na hone par bhi mail aaye, to niche wali line un-comment kar dein
                # send_email("LMS Check", "No pending tasks found today. Relax!")

        except Exception as e:
            print(f"An error occurred: {e}")
            
        browser.close()

if __name__ == "__main__":
    run_bot()
