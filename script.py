import os
import smtplib
from playwright.sync_api import sync_playwright
from email.message import EmailMessage
from datetime import datetime, timedelta
from dateutil import parser

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

def parse_task_date(date_str):
    try:
        # Parse date using dateutil parser
        parsed_date = parser.parse(date_str, fuzzy=True)
        return parsed_date.date()
    except Exception as e:
        print(f"Error parsing date '{date_str}': {e}")
        return None

def scrape_day_tasks(page, url):
    tasks = []
    try:
        print(f"Navigating to: {url}")
        page.goto(url, wait_until="load", timeout=90000)
        page.wait_for_timeout(7000)
        event_elements = page.query_selector_all('.event')
        for event in event_elements:
            full_text = event.inner_text()
            if "Add submission" in full_text:
                name_el = event.query_selector('h3')
                name = name_el.inner_text().strip() if name_el else "Unnamed Task"

                course_el = event.query_selector('.course') or event.query_selector('a[href*="course/view.php"]')
                course = course_el.inner_text().strip() if course_el else "LMS Course"

                # Extract date part carefully from full_text (remove "Add submission")
                date_text = full_text.replace("Add submission", "").strip()
                task_date = parse_task_date(date_text)
                if not task_date:
                    print(f"Skipping task due to date parsing issue: {full_text}")
                    continue

                tasks.append({'name': name, 'course': course, 'date': task_date.strftime("%A, %d %B %Y")})
    except Exception as e:
        print(f"Error scraping {url}: {e}")
    return tasks

def date_to_ts(d):
    # Convert date (without time) to timestamp for midnight UTC+5
    dt = datetime(d.year, d.month, d.day, 0, 0) - timedelta(hours=5)  # Convert to UTC for LMS URL
    return int(dt.timestamp())

def run_bot():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        context.set_default_timeout(60000)
        page = context.new_page()
        
        now_utc = datetime.utcnow()
        now_pak = now_utc + timedelta(hours=5)
        current_date = now_pak.date()
        current_hour = now_pak.hour
        current_minute = now_pak.minute

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

            # 5 PM alerts (16 to 19:59)
            if 16 <= current_hour < 20:
                combined_tasks = []

                if tasks_due_day_after:
                    for t in tasks_due_day_after:
                        t['status'] = "Due in 2 Days"
                    combined_tasks.extend(tasks_due_day_after)

                if tasks_due_tomorrow:
                    for t in tasks_due_tomorrow:
                        t['status'] = "Due Tomorrow"
                    combined_tasks.extend(tasks_due_tomorrow)

                if tasks_due_today:
                    for t in tasks_due_today:
                        t['status'] = "Due Today"
                    combined_tasks.extend(tasks_due_today)

                if combined_tasks:
                    send_professional_email(
                        "LMS Alert: Upcoming Deadlines",
                        "Upcoming Deadlines",
                        "You have pending tasks due soon. Please submit on time.",
                        combined_tasks,
                        "#0277bd"
                    )
                else:
                    print("No upcoming tasks, skipping 5 PM email.")

            # 10 AM alert (9 to 11:59, to allow late runs)
            elif 9 <= current_hour < 12:
                if tasks_due_today:
                    send_professional_email(
                        "LMS FINAL WARNING!",
                        "Deadline Today",
                        "Today is the last day to submit your tasks.",
                        tasks_due_today,
                        "#d32f2f"
                    )
                else:
                    print("No tasks due today, skipping 10 AM email.")

            # 11 PM alert (23:00 to 23:59)
            elif current_hour == 23:
                if tasks_due_today:
                    send_professional_email(
                        "LMS LAST ALERT!",
                        "Deadline Passing!",
                        "Submit your tasks immediately!",
                        tasks_due_today,
                        "#000000"
                    )
                else:
                    print("No tasks due today, skipping 11 PM email.")

        except Exception as e:
            print(f"Main execution error: {e}")
        
        browser.close()

if __name__ == "__main__":
    run_bot()

