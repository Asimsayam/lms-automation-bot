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

def send_professional_email(subject, title, subtitle, tasks, status_color):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = f"Superior LMS Assistant <{EMAIL_USER}>"
    msg['To'] = EMAIL_USER
    task_html = "".join([f"<div style='border-left: 5px solid {status_color}; padding: 15px; margin-bottom: 15px; background: #fafafa; border: 1px solid #eee; border-radius: 8px;'><strong style='font-size: 18px; color: #333;'>📌 {t['name']}</strong><br><div style='margin-top: 8px; color: #555; font-size: 14px;'>📖 <b>Course:</b> {t['course']}</div><div style='margin-top: 5px; color: {status_color}; font-weight: bold; font-size: 14px;'>⏰ <b>Deadline:</b><br>{t['date']}</div></div>" for t in tasks]) if tasks else "<p>✅ All Clear!</p>"
    html_content = f"<html><body style='font-family: Segoe UI, sans-serif; background-color: #f4f7f6; padding: 20px;'><div style='max-width: 600px; margin: auto; background: white; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.15); overflow: hidden;'><div style='background: {status_color}; color: white; padding: 30px; text-align: center;'><h1 style='margin: 0;'>{title}</h1><p style='margin: 5px 0 0; opacity: 0.9;'>{subtitle}</p></div><div style='padding: 30px;'><p>Asalam-o-Alaikum Asim,</p>{task_html}<div style='text-align: center; margin-top: 30px;'><a href='https://lms.superior.edu.pk/my/' style='background: {status_color}; color: white; padding: 12px 25px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;'>Open Superior LMS</a></div></div><div style='background: #f1f1f1; color: #888; padding: 15px; text-align: center; font-size: 12px;'>Superior LMS Automated Assistant</div></div></body></html>"
    msg.add_alternative(html_content, subtype='html')
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_USER, EMAIL_PASS)
        smtp.send_message(msg)

def scrape_day_tasks(page, url):
    tasks = []
    try:
        page.goto(url, wait_until="load", timeout=60000)
        page.wait_for_timeout(5000)
        event_elements = page.query_selector_all('.event')
        for event in event_elements:
            full_text = event.inner_text()
            
            # --- THE "GO TO ACTIVITY" FILTER ---
            # Agar 'Add submission' nahi hai aur 'Go to activity' hai, to matlab task DONE hai.
            if "Add submission" not in full_text:
                print(f"Skipping {event.query_selector('h3').inner_text()}: Task already submitted.")
                continue 
            
            name = event.query_selector('h3').inner_text().strip()
            course = "Course Detail in LMS"
            course_el = event.query_selector('.course') or event.query_selector('a[href*="course/view.php"]')
            if course_el: course = course_el.inner_text().strip()
            
            # Clean the date text for email
            deadline_info = full_text.replace("Add submission", "").strip()
            tasks.append({'name': name, 'course': course, 'date': deadline_info})
    except: pass
    return tasks

def run_bot():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        now_pak = datetime.utcnow() + timedelta(hours=5)
        current_hour = now_pak.hour
        tomorrow_ts = int((datetime.utcnow() + timedelta(hours=5, days=1)).timestamp())
        two_days_ts = int((datetime.utcnow() + timedelta(hours=5, days=2)).timestamp())

        try:
            page.goto("https://lms.superior.edu.pk/login/index.php")
            page.fill('#username', LMS_USER)
            page.fill('#password', LMS_PASS)
            page.keyboard.press("Enter")
            page.wait_for_load_state("networkidle")

            tasks_today = scrape_day_tasks(page, "https://lms.superior.edu.pk/calendar/view.php?view=day")
            tasks_tomorrow = scrape_day_tasks(page, f"https://lms.superior.edu.pk/calendar/view.php?view=day&time={tomorrow_ts}")
            tasks_upcoming = scrape_day_tasks(page, f"https://lms.superior.edu.pk/calendar/view.php?view=day&time={two_days_ts}")

            if 9 <= current_hour <= 11:
                if tasks_today: send_professional_email("LMS Alert: Due Today!", "Tasks Due Today!", "Action required by tonight.", tasks_today, "#d32f2f")
                else: send_professional_email("LMS Status: All Clear ✅", "Good Morning Asim!", "No pending deadlines for today.", [], "#2e7d32")
            elif 16 <= current_hour <= 18:
                if tasks_today: send_professional_email("LMS Evening Reminder", "Still Pending Today!", "Please submit before midnight.", tasks_today, "#f57c00")
                elif tasks_tomorrow: send_professional_email("LMS Alert: Due Tomorrow!", "Deadline Tomorrow", "1 day left to submit.", tasks_tomorrow, "#673ab7")
                elif tasks_upcoming: send_professional_email("LMS Alert: 2 Days Left", "Upcoming Deadline", "Due in 2 days.", tasks_upcoming, "#0277bd")
                else: send_professional_email("LMS Evening Status ✅", "All Clear", "Checked your LMS, no urgent tasks.", [], "#2e7d32")
            elif current_hour >= 22 and tasks_today:
                send_professional_email("LMS FINAL WARNING! 🚨", "Closing Soon!", "This is your last chance.", tasks_today, "#212121")

        except Exception as e: print(f"Error: {e}")
        browser.close()

if __name__ == "__main__":
    run_bot()
