import os
import smtplib
from playwright.sync_api import sync_playwright
from email.message import EmailMessage
from datetime import datetime, timedelta

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
            f"⏰ <b>Deadline:</b><br>{t['date'].strftime('%Y-%m-%d')}</div></div>" for t in tasks])
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

def parse_date_from_text(date_text):
    # Expected date_text format is something like "8 February 2026" or "8 Feb 2026"
    # Try to parse it safely
    from dateutil import parser
    try:
        dt = parser.parse(date_text, dayfirst=True)
        return dt.date()
    except Exception as e:
        print(f"Error parsing date '{date_text}': {e}")
        return None

def scrape_pending_tasks(page, url):
    tasks = []
    try:
        print(f"Navigating to: {url}")
        page.goto(url, wait_until="load", timeout=90000)
        page.wait_for_timeout(5000)  # Wait for JS to load events

        event_elements = page.query_selector_all('.event')
        for event in event_elements:
            full_text = event.inner_text()
            # Only pending tasks have "Add submission"
            if "Add submission" in full_text:
                # Extract task name
                name_el = event.query_selector('h3')
                name = name_el.inner_text().strip() if name_el else "Unnamed Task"

                # Extract course name
                course_el = event.query_selector('.course') or event.query_selector('a[href*="course/view.php"]')
                course = course_el.inner_text().strip() if course_el else "LMS Course"

                # Extract date text (remove 'Add submission')
                date_text = full_text.replace("Add submission", "").strip()

                # Parse date from date_text (you might have to customize parsing as per LMS)
                due_date = parse_date_from_text(date_text)
                if due_date:
                    tasks.append({'name': name, 'course': course, 'date': due_date})
                else:
                    print(f"Skipping task due to date parsing issue: {name}")

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

        # For scraping, get calendar pages for next 3 days:
        def date_to_ts(d):
            # Timestamp at midnight UTC+5 (Pakistan time)
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

            # Scrape all pending tasks for today, tomorrow and day after tomorrow
            tasks_today = scrape_pending_tasks(page, f"https://lms.superior.edu.pk/calendar/view.php?view=day&time={today_ts}")
            tasks_tomorrow = scrape_pending_tasks(page, f"https://lms.superior.edu.pk/calendar/view.php?view=day&time={tomorrow_ts}")
            tasks_day_after = scrape_pending_tasks(page, f"https://lms.superior.edu.pk/calendar/view.php?view=day&time={day_after_tomorrow_ts}")

            all_tasks = tasks_today + tasks_tomorrow + tasks_day_after

            # Filter tasks with due dates only (just to be safe)
            all_tasks = [t for t in all_tasks if isinstance(t.get('date'), datetime.date)]

            # Group tasks by how many days left to submit:
            tasks_by_days_left = {0: [], 1: [], 2: []}
            for t in all_tasks:
                days_left = (t['date'] - current_date).days
                if days_left in tasks_by_days_left:
                    tasks_by_days_left[days_left].append(t)

            # Now logic for emails:

            # 5 PM alert window (16:00 to 20:00)
            if 16 <= current_hour < 20:
                # Priority: tasks due in 2 days first
                if tasks_by_days_left[2]:
                    send_professional_email(
                        "LMS Alert: Tasks Due in 2 Days",
                        "Upcoming Deadlines",
                        "You have tasks due in 2 days.",
                        tasks_by_days_left[2],
                        "#0277bd"
                    )
                    return

                # Then tasks due in 1 day
                if tasks_by_days_left[1]:
                    send_professional_email(
                        "LMS Alert: Tasks Due Tomorrow",
                        "Deadline Tomorrow",
                        "You have tasks due tomorrow.",
                        tasks_by_days_left[1],
                        "#673ab7"
                    )
                    return

                # Then tasks due today
                if tasks_by_days_left[0]:
                    send_professional_email(
                        "LMS Evening Reminder",
                        "Tasks Due Today",
                        "Submit your tasks ASAP!",
                        tasks_by_days_left[0],
                        "#f57c00"
                    )
                    return

            # 10 AM alert window (9:00 to 12:00)
            elif 9 <= current_hour < 12:
                if tasks_by_days_left[0]:
                    send_professional_email(
                        "LMS FINAL WARNING!",
                        "Deadline Today",
                        "Today is the last day to submit your tasks.",
                        tasks_by_days_left[0],
                        "#d32f2f"
                    )
                    return
                if not (tasks_by_days_left[0] or tasks_by_days_left[1] or tasks_by_days_left[2]):
                    send_professional_email(
                        "LMS Status: All Clear ✅",
                        "Good Morning!",
                        "No pending tasks at the moment.",
                        [],
                        "#2e7d32"
                    )
                    return

            # 11 PM alert window (23:00 to 23:59)
            elif 23 <= current_hour <= 23:
                if tasks_by_days_left[0]:
                    send_professional_email(
                        "LMS LAST ALERT!",
                        "Deadline Passing!",
                        "Submit your tasks immediately!",
                        tasks_by_days_left[0],
                        "#000000"
                    )
                    return

        except Exception as e:
            print(f"Main execution error: {e}")

        browser.close()

if __name__ == "__main__":
    run_bot()

