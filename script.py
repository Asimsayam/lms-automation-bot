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
        task_html = "<p style='color: #2e7d32; font-size: 16px;'>✅ All Clear! No pending tasks found for this day.</p>"
    else:
        for t in tasks:
            task_html += f"""
            <div style='border-left: 5px solid {status_color}; padding: 15px; margin-bottom: 15px; background: #fafafa; border: 1px solid #eee; border-radius: 5px;'>
                <strong style='font-size: 18px; color: #333;'>📌 {t['name']}</strong><br>
                <div style='margin-top: 5px; color: #555; font-size: 14px;'>📖 <b>Course:</b> {t['course']}</div>
                <div style='color: {status_color}; font-weight: bold; font-size: 14px;'>⏰ <b>Deadline:</b> {t['date']}</div>
            </div>
            """

    html_content = f"""
    <html>
    <body style='font-family: "Segoe UI", Arial, sans-serif; background-color: #f4f7f6; padding: 20px;'>
        <div style='max-width: 600px; margin: auto; background: white; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); overflow: hidden;'>
            <div style='background: {status_color}; color: white; padding: 30px; text-align: center;'>
                <h1 style='margin: 0;'>{title}</h1>
                <p style='margin: 5px 0 0; opacity: 0.9;'>{subtitle}</p>
            </div>
            <div style='padding: 30px;'>
                <p>Asalam-o-Alaikum Asim,</p>
                {task_html}
                <div style='text-align: center; margin-top: 30px;'>
                    <a href='https://lms.superior.edu.pk/my/' style='background: {status_color}; color: white; padding: 12px 25px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;'>Open Superior LMS</a>
                </div>
            </div>
            <div style='background: #eee; color: #777; padding: 15px; text-align: center; font-size: 12px;'>
                Superior University Automated Assistant Update
            </div>
        </div>
    </body>
    </html>
    """
    msg.add_alternative(html_content, subtype='html')
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_USER, EMAIL_PASS)
        smtp.send_message(msg)

def get_day_tasks(page, url):
    tasks = []
    try:
        page.goto(url, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(5000)
        # Asli task boxes dhoondna (.event class)
        elements = page.query_selector_all('.event')
        for el in elements:
            name = el.query_selector('h3').inner_text().strip()
            course = "Subject Detail in LMS"
            course_el = el.query_selector('.course') or el.query_selector('a[href*="course/view.php"]')
            if course_el: course = course_el.inner_text().strip()
            
            # Deadline time nikalna
            time_info = el.inner_text().split('Deadline:')[1].split('\n')[0].strip() if 'Deadline:' in el.inner_text() else "11:59 PM"
            tasks.append({'name': name, 'course': course, 'date': time_info})
    except: pass
    return tasks

def run_bot():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        now_pak = datetime.utcnow() + timedelta(hours=5)
        current_hour = now_pak.hour
        
        # Timestamps for Today, Tomorrow, and 2nd Day
        today_ts = int(now_pak.timestamp())
        tomorrow_ts = int((now_pak + timedelta(days=1)).timestamp())
        two_days_ts = int((now_pak + timedelta(days=2)).timestamp())

        try:
            # Login
            page.goto("https://lms.superior.edu.pk/login/index.php")
            page.fill('#username', LMS_USER)
            page.fill('#password', LMS_PASS)
            page.keyboard.press("Enter")
            page.wait_for_load_state("networkidle")

            # Get Tasks for specific days
            tasks_today = get_day_tasks(page, f"https://lms.superior.edu.pk/calendar/view.php?view=day&time={today_ts}")
            tasks_tomorrow = get_day_tasks(page, f"https://lms.superior.edu.pk/calendar/view.php?view=day&time={tomorrow_ts}")
            tasks_upcoming = get_day_tasks(page, f"https://lms.superior.edu.pk/calendar/view.php?view=day&time={two_days_ts}")

            # --- RULES ENGINE ---
            if 9 <= current_hour <= 11: # 10 AM
                if tasks_today:
                    send_professional_email("LMS Alert: Due Today!", "Urgent: Tasks Due Today", "Please submit by tonight.", tasks_today, "#d32f2f")
                else:
                    send_professional_email("LMS Status: All Clear ✅", "Good Morning Asim!", "No deadlines for today.", [], "#2e7d32")

            elif 16 <= current_hour <= 18: # 5 PM
                if tasks_today:
                    send_professional_email("LMS Evening Reminder", "Still Pending!", "Final reminders for today.", tasks_today, "#f57c00")
                elif tasks_tomorrow:
                    send_professional_email("LMS Alert: Due Tomorrow!", "Deadline Approaching", "1 day left to submit.", tasks_tomorrow, "#673ab7")
                elif tasks_upcoming:
                    send_professional_email("LMS Alert: 2 Days Left", "Upcoming Deadline", "Due in 2 days.", tasks_upcoming, "#0277bd")
                else:
                    send_professional_email("LMS Evening Status ✅", "All Clear", "No urgent deadlines found.", [], "#2e7d32")

            elif current_hour >= 21 and tasks_today: # 11 PM
                send_professional_email("LMS FINAL WARNING! 🚨", "Closing Soon!", "Last chance to upload.", tasks_today, "#212121")

        except Exception as e: print(f"Error: {e}")
        browser.close()

if __name__ == "__main__":
    run_bot()
