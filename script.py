import os
import smtplib
from playwright.sync_api import sync_playwright
from email.message import EmailMessage
from datetime import datetime, timedelta

# Credentials from GitHub Secrets
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
        task_html = "<p style='color: #28a745; font-size: 16px;'>✅ No pending tasks found for this category. Stay relaxed!</p>"
    else:
        for t in tasks:
            task_html += f"""
            <div style='border-left: 5px solid {status_color}; padding: 15px; margin-bottom: 12px; background: #fdfdfd; border-radius: 4px; border: 1px solid #eee; border-left-color: {status_color};'>
                <strong style='font-size: 18px; color: #333;'>{t['name']}</strong><br>
                <span style='color: #555; font-size: 14px;'>📖 Course: {t['course']}</span><br>
                <span style='color: {status_color}; font-weight: bold; font-size: 14px;'>⏰ Deadline: {t['date']}</span>
            </div>
            """

    html_content = f"""
    <html>
    <body style='font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; padding: 20px;'>
        <div style='max-width: 600px; margin: auto; background: white; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); overflow: hidden;'>
            <div style='background: {status_color}; color: white; padding: 30px; text-align: center;'>
                <h1 style='margin: 0; font-size: 24px;'>{title}</h1>
                <p style='margin: 5px 0 0; opacity: 0.9;'>{subtitle}</p>
            </div>
            <div style='padding: 30px;'>
                <p style='font-size: 16px;'>Asalam-o-Alaikum,</p>
                <p style='font-size: 15px; color: #666;'>Here is your LMS activity report generated on {datetime.now().strftime('%d %B, %Y')}:</p>
                {task_html}
                <div style='text-align: center; margin-top: 30px;'>
                    <a href='https://lms.superior.edu.pk/my/' style='background: {status_color}; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;'>Login to LMS</a>
                </div>
            </div>
            <div style='background: #f9f9f9; color: #999; padding: 15px; text-align: center; font-size: 12px;'>
                Superior University Automated Assistant • This is a scheduled update.
            </div>
        </div>
    </body>
    </html>
    """
    msg.add_alternative(html_content, subtype='html')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_USER, EMAIL_PASS)
            smtp.send_message(msg)
        print(f"Professional Email Sent: {subject}")
    except Exception as e:
        print(f"Email failed: {e}")

def run_bot():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        now_pak = datetime.utcnow() + timedelta(hours=5)
        current_hour = now_pak.hour
        today_str = now_pak.strftime("%-d %B")
        two_days_str = (now_pak + timedelta(days=2)).strftime("%-d %B")

        try:
            page.goto("https://lms.superior.edu.pk/login/index.php", wait_until="networkidle")
            page.fill('input[name="username"]', LMS_USER)
            page.fill('input[name="password"]', LMS_PASS)
            page.keyboard.press("Enter")
            
            # Wait for content to load properly
            page.wait_for_timeout(15000)

            urgent_tasks = []
            upcoming_tasks = []
            
            # Target the specific timeline elements
            items = page.query_selector_all('.timeline-event-list-item')
            for item in items:
                name = item.query_selector('.event-name').inner_text().strip()
                date_text = item.query_selector('.small.text-muted').inner_text().strip()
                course = "Course Detail Not Found"
                course_el = item.query_selector('a[href*="course/view.php"]')
                if course_el: course = course_el.inner_text().split('|')[0].strip()
                
                task_data = {'name': name, 'course': course, 'date': date_text}
                
                if "Today" in date_text or today_str in date_text:
                    urgent_tasks.append(task_data)
                elif two_days_str in date_text:
                    upcoming_tasks.append(task_data)

            # --- APPLIED RULES ---

            # RULE 1: MORNING 10 AM (Hour 10)
            if 9 <= current_hour <= 11:
                if urgent_tasks:
                    send_professional_email("LMS URGENT: Due Today!", "Daily Task Alert", "These tasks are ending today!", urgent_tasks, "#d32f2f")
                else:
                    send_professional_email("LMS Status: All Clear ✅", "No Tasks Today", "You have no deadlines ending today.", [], "#2e7d32")

            # RULE 2: EVENING 5 PM (Hour 17)
            elif 16 <= current_hour <= 18:
                if urgent_tasks:
                    send_professional_email("LMS Evening Reminder", "Incomplete Tasks!", "Still pending for today!", urgent_tasks, "#f57c00")
                elif upcoming_tasks:
                    send_professional_email("LMS Alert: 2 Days Left", "Upcoming Deadline", "You need to upload this in 2 days.", upcoming_tasks, "#1976d2")

            # RULE 3: NIGHT 11 PM (Hour 23)
            elif current_hour >= 22:
                if urgent_tasks:
                    send_professional_email("LMS FINAL WARNING! 🚨", "Last Chance to Submit", "Deadlines closing soon!", urgent_tasks, "#000000")

        except Exception as e:
            print(f"Bot failed or no tasks: {e}")
        
        browser.close()

if __name__ == "__main__":
    run_bot()
