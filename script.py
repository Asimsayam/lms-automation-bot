import os
import smtplib
from playwright.sync_api import sync_playwright
from email.message import EmailMessage
from datetime import datetime, timedelta
import dateutil.parser

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

def extract_due_date(text):
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        try:
            # Parse line if it contains a recognizable date/time
            parsed_date = dateutil.parser.parse(line, fuzzy=True, default=datetime.now())
            # Check if parsed_date is reasonable (not too old)
            if parsed_date > datetime.now() - timedelta(days=1):
                return parsed_date
        except Exception:
            continue
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
            # Only consider tasks with "Add submission" (pending tasks)
            if "Add submission" in full_text:
                name_el = event.query_selector('h3')
                name = name_el.inner_text().strip() if name_el else "Unnamed Task"
                course_el = event.query_selector('.course') or event.query_selector('a[href*="course/view.php"]')
                course = course_el.inner_text().strip() if course_el else "LMS Course"

                due_date = extract_due_date(full_text)
                if not due_date:
                    print(f"Skipping task due to date parsing issue: {name}")
                    continue

                date_text = due_date.strftime("%A, %d %B %Y, %I:%M %p")
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

            # Flatten all tasks for combined checking
            all_pending_tasks = tasks_due_today + tasks_due_tomorrow + tasks_due_day_after

            # Filter by due dates for alert logic
            def filter_tasks_by_due(tasks, days_ahead):
                now = now_pak.replace(hour=0, minute=0, second=0, microsecond=0)
                filtered = []
                for t in tasks:
                    due_dt = datetime.strptime(t['date'], "%A, %d %B %Y, %I:%M %p")
                    delta_days = (due_dt.date() - now.date()).days
                    if delta_days == days_ahead:
                        filtered.append(t)
                return filtered

            # Check submissions per day and only alert if still pending
            # 5 PM Alert - show tasks due in 2 days or 1 day or today in that order
            if 16 <= current_hour <= 20:  # 4 PM to 8 PM to allow some flexibility
                tasks_due_in_2_days = filter_tasks_by_due(all_pending_tasks, 2)
                if tasks_due_in_2_days:
                    send_professional_email(
                        "LMS Alert: Tasks Due in 2 Days",
                        "Upcoming Deadlines",
                        "You have tasks due in 2 days.",
                        tasks_due_in_2_days,
                        "#0277bd"
                    )
                    return

                tasks_due_tomorrow_only = filter_tasks_by_due(all_pending_tasks, 1)
                if tasks_due_tomorrow_only:
                    send_professional_email(
                        "LMS Alert: Tasks Due Tomorrow",
                        "Deadline Tomorrow",
                        "You have tasks due tomorrow.",
                        tasks_due_tomorrow_only,
                        "#673ab7"
                    )
                    return

                tasks_due_today_only = filter_tasks_by_due(all_pending_tasks, 0)
                if tasks_due_today_only:
                    send_professional_email(
                        "LMS Evening Reminder",
                        "Tasks Due Today",
                        "Submit your tasks ASAP!",
                        tasks_due_today_only,
                        "#f57c00"
                    )
                    return

            # 10 AM Alert
            elif 9 <= current_hour <= 12:  # 9 AM to 11 AM window
                tasks_due_today_only = filter_tasks_by_due(all_pending_tasks, 0)
                if tasks_due_today_only:
                    send_professional_email(
                        "LMS FINAL WARNING!",
                        "Deadline Today",
                        "Today is the last day to submit your tasks.",
                        tasks_due_today_only,
                        "#d32f2f"
                    )
                    return
                if not all_pending_tasks:
                    send_professional_email(
                        "LMS Status: All Clear ✅",
                        "Good Morning!",
                        "No pending tasks at the moment.",
                        [],
                        "#2e7d32"
                    )
                    return

            # 11 PM Alert
            elif 22 <= current_hour <= 23:  # 10 PM to 11 PM window
                tasks_due_today_only = filter_tasks_by_due(all_pending_tasks, 0)
                if tasks_due_today_only:
                    send_professional_email(
                        "LMS LAST ALERT!",
                        "Deadline Passing!",
                        "Submit your tasks immediately!",
                        tasks_due_today_only,
                        "#000000"
                    )
                    return

        except Exception as e:
            print(f"Main execution error: {e}")

        browser.close()

if __name__ == "__main__":
    run_bot()

