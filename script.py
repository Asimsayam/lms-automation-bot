import os
import smtplib
from playwright.sync_api import sync_playwright
from email.message import EmailMessage
from datetime import datetime, timedelta
from dateutil.parser import parse

# Credentials from environment variables
LMS_USER = os.environ.get('LMS_USER')
LMS_PASS = os.environ.get('LMS_PASS')
EMAIL_USER = os.environ.get('EMAIL_USER')
EMAIL_PASS = os.environ.get('EMAIL_PASS')

def send_professional_email(subject, title, subtitle, tasks, status_color):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = f"Superior LMS Assistant <{EMAIL_USER}>"
    msg['To'] = EMAIL_USER

    if tasks:
        task_html = "".join([
            f"<div style='border-left: 5px solid {status_color}; padding: 15px; margin-bottom: 15px; "
            f"background: #fafafa; border: 1px solid #eee; border-radius: 8px;'>"
            f"<strong style='font-size: 18px; color: #333;'>📌 {t['name']}</strong><br>"
            f"<div style='margin-top: 8px; color: #555; font-size: 14px;'>📖 <b>Course:</b> {t['course']}</div>"
            f"<div style='margin-top: 5px; color: {status_color}; font-weight: bold; font-size: 14px;'>"
            f"⏰ <b>Deadline:</b><br>{t['date']}</div></div>" for t in tasks])
    else:
        task_html = "<p>✅ All Clear! No pending tasks.</p>"

    html_content = f"""
    <html>
    <body style='font-family: Arial, sans-serif; background-color: #f4f7f6; padding: 20px;'>
    <div style='max-width: 600px; margin: auto; background: white; border-radius: 12px; border: 1px solid #ddd; 
        overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1);'>
        <div style='background: {status_color}; color: white; padding: 25px; text-align: center;'>
            <h2 style='margin: 0;'>{title}</h2>
            <p style='margin: 5px 0 0; opacity: 0.9;'>{subtitle}</p>
        </div>
        <div style='padding: 25px;'>
            <p>Asalam-o-Alaikum Asim,</p>
            <p style='font-size: 15px;'>Here is your LMS report:</p>
            {task_html}
        </div>
        <div style='background: #f9f9f9; padding: 15px; text-align: center; font-size: 12px; color: #888;'>
            Superior Automated Assistant
        </div>
    </div>
    </body>
    </html>
    """
    msg.add_alternative(html_content, subtype='html')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_USER, EMAIL_PASS)
        smtp.send_message(msg)
    print(f"Email sent: {subject}")

def scrape_day_tasks(page, url):
    tasks = []
    try:
        print(f"Navigating to: {url}")
        page.goto(url, wait_until="load", timeout=90000)
        page.wait_for_timeout(7000)
        event_elements = page.query_selector_all('.event')
        for event in event_elements:
            full_text = event.inner_text()
            # Only consider tasks with "Add submission" (pending tasks)
            if "Add submission" in full_text:
                name_el = event.query_selector('h3')
                name = name_el.inner_text().strip() if name_el else "Unnamed Task"
                course_el = event.query_selector('.course') or event.query_selector('a[href*="course/view.php"]')
                course = course_el.inner_text().strip() if course_el else "LMS Course"
                date_text = full_text.replace("Add submission", "").strip()
                tasks.append({'name': name, 'course': course, 'date': date_text})
    except Exception as e:
        print(f"Error scraping {url}: {e}")
    return tasks

def run_bot():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        context.set_default_timeout(60000)
        page = context.new_page()

        now_pak = datetime.utcnow() + timedelta(hours=5)
        current_date = now_pak.date()
        current_hour = now_pak.hour

        def date_to_ts(d):
            return int(datetime(d.year, d.month, d.day, 0, 0).timestamp())

        today_ts = date_to_ts(current_date)
        tomorrow_ts = date_to_ts(current_date + timedelta(days=1))
        day_after_tomorrow_ts = date_to_ts(current_date + timedelta(days=2))

        try:
            print(f"LMS Check started at {now_pak.strftime('%Y-%m-%d %H:%M')}...")
            page.goto("https://lms.superior.edu.pk/login/index.php", timeout=90000)
            page.fill('input[name="username"]', LMS_USER)
            page.fill('input[name="password"]', LMS_PASS)
            page.keyboard.press("Enter")
            page.wait_for_load_state("networkidle")
            print("Login successful.")

            tasks_due_today = scrape_day_tasks(page, f"https://lms.superior.edu.pk/calendar/view.php?view=day&time={today_ts}")
            tasks_due_tomorrow = scrape_day_tasks(page, f"https://lms.superior.edu.pk/calendar/view.php?view=day&time={tomorrow_ts}")
            tasks_due_day_after = scrape_day_tasks(page, f"https://lms.superior.edu.pk/calendar/view.php?view=day&time={day_after_tomorrow_ts}")

            combined_tasks_5pm = tasks_due_day_after + tasks_due_tomorrow + tasks_due_today
            combined_tasks_10am = tasks_due_today
            combined_tasks_11pm = tasks_due_today

            if 9 <= current_hour <= 12:
                # 10 AM time window email (flexible 9-12)
                if combined_tasks_10am:
                    send_professional_email(
                        "LMS FINAL WARNING!",
                        "Deadline Today",
                        "Today is the last day to submit your tasks.",
                        combined_tasks_10am,
                        "#d32f2f"
                    )
                else:
                    send_professional_email(
                        "LMS Status: All Clear ✅",
                        "Good Morning!",
                        "No pending tasks at the moment.",
                        [],
                        "#2e7d32"
                    )
                return

            if 16 <= current_hour <= 20:
                # 5 PM time window email (flexible 4-8)
                if combined_tasks_5pm:
                    send_professional_email(
                        "LMS Alert: Upcoming Deadlines",
                        "Upcoming Deadlines",
                        "You have tasks due soon. Please submit on time.",
                        combined_tasks_5pm,
                        "#0277bd"
                    )
                else:
                    print("No upcoming tasks, skipping 5 PM email.")
                return

            if 23 <= current_hour <24:
                # 11 PM time window email (exactly 11)
                if combined_tasks_11pm:
                    send_professional_email(
                        "LMS LAST ALERT!",
                        "Deadline Passing!",
                        "Submit your tasks immediately!",
                        combined_tasks_11pm,
                        "#000000"
                    )
                return

        except Exception as e:
            print(f"Main execution error: {e}")

        browser.close()

if __name__ == "__main__":
    run_bot()


