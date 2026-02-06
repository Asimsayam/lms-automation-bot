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
    task_html = ""
    if not tasks:
        task_html = f"<p style='color: #2e7d32; font-size: 16px;'>✅ No pending tasks found for this category.</p>"
    else:
        for t in tasks:
            task_html += f"""
            <div style='border-left: 5px solid {status_color}; padding: 15px; margin-bottom: 15px; background: #fafafa; border: 1px solid #eee; border-left-color: {status_color}; border-radius: 5px;'>
                <strong style='font-size: 18px; color: #333;'>📌 {t['name']}</strong><br>
                <div style='margin-top: 5px; color: #555; font-size: 14px;'>📖 <b>Course:</b> {t['course']}</div>
                <div style='color: {status_color}; font-weight: bold; font-size: 14px;'>⏰ <b>Deadline:</b> {t['date']}</div>
            </div>
            """
    html_content = f"<html><body style='font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px;'><div style='max-width: 600px; margin: auto; background: white; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); overflow: hidden;'><div style='background: {status_color}; color: white; padding: 30px; text-align: center;'><h1 style='margin: 0;'>{title}</h1><p style='margin: 5px 0 0; opacity: 0.9;'>{subtitle}</p></div><div style='padding: 30px;'><p>Asalam-o-Alaikum Asim,</p>{task_html}<div style='text-align: center; margin-top: 30px;'><a href='https://lms.superior.edu.pk/my/' style='background: {status_color}; color: white; padding: 12px 25px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;'>Open Superior LMS</a></div></div><div style='background: #f1f1f1; color: #777; padding: 15px; text-align: center; font-size: 12px;'>Superior University Automated Assistant</div></div></body></html>"
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
            name = event.query_selector('h3').inner_text().strip()
            course = "Not Specified"
            course_el = event.query_selector('.course') or event.query_selector('a[href*="course/view.php"]')
            if course_el: course = course_el.inner_text().strip()
            deadline = event.inner_text().strip()
            tasks.append({'name': name, 'course': course, 'date': deadline})
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

            urgent_tasks = scrape_day_tasks(page, "https://lms.superior.edu.pk/calendar/view.php?view=day")
            tomorrow_tasks = scrape_day_tasks(page, f"https://lms.superior.edu.pk/calendar/view.php?view=day&time={tomorrow_ts}")
            upcoming_tasks = scrape_day_tasks(page, f"https://lms.superior.edu.pk/calendar/view.php?view=day&time={two_days_ts}")

            # 10 AM Logic
            if 9 <= current_hour <= 11:
                if urgent_tasks:
                    send_professional_email("LMS Alert: Due Today!", "Tasks Due Today!", "Action required by tonight.", urgent_tasks, "#d32f2f")
                else:
                    send_professional_email("LMS Status: All Clear ✅", "Good Morning!", "No tasks due today.", [], "#2e7d32")

            # 5 PM Logic
            elif 16 <= current_hour <= 18:
                if urgent_tasks:
                    send_professional_email("LMS Evening Reminder", "Still Pending!", "Submit before midnight!", urgent_tasks, "#f57c00")
                elif tomorrow_tasks:
                    send_professional_email("LMS Alert: Due Tomorrow!", "Deadline Approaching", "You have a task due tomorrow.", tomorrow_tasks, "#673ab7")
                elif upcoming_tasks:
                    send_professional_email("LMS Alert: 2 Days Left", "Upcoming Deadline", "Due in 2 days.", upcoming_tasks, "#0277bd")
                else:
                    send_professional_email("LMS Evening Status ✅", "All Clear", "No urgent deadlines found.", [], "#2e7d32")

            # 11 PM Logic
            elif current_hour >= 22 and urgent_tasks:
                send_professional_email("LMS FINAL WARNING! 🚨", "Closing Soon!", "Last chance to upload.", urgent_tasks, "#212121")

        except Exception as e: print(f"Failed: {e}")
        browser.close()

if __name__ == "__main__":
    run_bot()
