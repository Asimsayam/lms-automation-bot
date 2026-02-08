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
    print(f"[DEBUG] Preparing to send email with subject: {subject}")
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

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_USER, EMAIL_PASS)
            smtp.send_message(msg)
        print(f"[DEBUG] Email sent successfully: {subject}")
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")

def scrape_day_tasks(page, url):
    tasks = []
    try:
        print(f"[DEBUG] Navigating to: {url}")
        page.goto(url, wait_until="load", timeout=90000)
        page.wait_for_timeout(7000)
        event_elements = page.query_selector_all('.event')
        print(f"[DEBUG] Found {len(event_elements)} event elements.")
        for event in event_elements:
            full_text = event.inner_text()
            if "Add submission" in full_text:
                name_el = event.query_selector('h3')
                name = name_el.inner_text().strip() if name_el else "Unnamed Task"
                course_el = event.query_selector('.course') or event.query_selector('a[href*="course/view.php"]')
                course = course_el.inner_text().strip() if course_el else "LMS Course"
                date_text = full_text.replace("Add submission", "").strip()
                tasks.append({'name': name, 'course': course, 'date': date_text})
        print(f"[DEBUG] Tasks found: {len(tasks)}")
    except Exception as e:
        print(f"[ERROR] Error scraping {url}: {e}")
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
        now_minute = now_pak.minute

        print(f"[DEBUG] Current Pakistan time: {now_pak.strftime('%Y-%m-%d %H:%M')}, current_hour={current_hour}, current_minute={now_minute}")

        def date_to_ts(d):
            # Convert date (without time) to timestamp for midnight UTC+5
            return int(datetime(d.year, d.month, d.day, 0, 0).timestamp())

        today_ts = date_to_ts(current_date)
        tomorrow_ts = date_to_ts(current_date + timedelta(days=1))
        day_after_tomorrow_ts = date_to_ts(current_date + timedelta(days=2))

        try:
            print(f"[DEBUG] Starting LMS Check...")
            page.goto("https://lms.superior.edu.pk/login/index.php", timeout=90000)
            page.fill('input[name="username"]', LMS_USER)
            page.fill('input[name="password"]', LMS_PASS)
            page.keyboard.press("Enter")
            page.wait_for_load_state("networkidle")
            print("[DEBUG] Login successful.")

            tasks_due_today = scrape_day_tasks(page, f"https://lms.superior.edu.pk/calendar/view.php?view=day&time={today_ts}")
            tasks_due_tomorrow = scrape_day_tasks(page, f"https://lms.superior.edu.pk/calendar/view.php?view=day&time={tomorrow_ts}")
            tasks_due_day_after = scrape_day_tasks(page, f"https://lms.superior.edu.pk/calendar/view.php?view=day&time={day_after_tomorrow_ts}")

            print(f"[DEBUG] Tasks Today: {len(tasks_due_today)}, Tomorrow: {len(tasks_due_tomorrow)}, Day After Tomorrow: {len(tasks_due_day_after)}")

            # Define flexible alert windows:
            morning_alert = (9 <= current_hour <= 11)
            evening_alert = (16 <= current_hour <= 19)
            last_alert = (current_hour == 10 and now_minute >= 30) or (current_hour == 11 and now_minute <= 55)

            if evening_alert:
                if tasks_due_day_after:
                    send_professional_email(
                        "LMS Alert: Tasks Due in 2 Days",
                        "Upcoming Deadlines",
                        "You have tasks due in 2 days.",
                        tasks_due_day_after,
                        "#0277bd"
                    )
                    return
                if tasks_due_tomorrow:
                    send_professional_email(
                        "LMS Alert: Tasks Due Tomorrow",
                        "Deadline Tomorrow",
                        "You have tasks due tomorrow.",
                        tasks_due_tomorrow,
                        "#673ab7"
                    )
                    return
                if tasks_due_today:
                    send_professional_email(
                        "LMS Evening Reminder",
                        "Tasks Due Today",
                        "Submit your tasks ASAP!",
                        tasks_due_today,
                        "#f57c00"
                    )
                    return

            elif morning_alert:
                if tasks_due_today:
                    send_professional_email(
                        "LMS FINAL WARNING!",
                        "Deadline Today",
                        "Today is the last day to submit your tasks.",
                        tasks_due_today,
                        "#d32f2f"
                    )
                    return
                if not (tasks_due_today or tasks_due_tomorrow or tasks_due_day_after):
                    send_professional_email(
                        "LMS Status: All Clear ✅",
                        "Good Morning!",
                        "No pending tasks at the moment.",
                        [],
                        "#2e7d32"
                    )
                    return

            elif last_alert:
                if tasks_due_today:
                    send_professional_email(
                        "LMS LAST ALERT!",
                        "Deadline Passing!",
                        "Submit your tasks immediately!",
                        tasks_due_today,
                        "#000000"
                    )
                    return

        except Exception as e:
            print(f"[ERROR] Main execution error: {e}")
        
        browser.close()

if __name__ == "__main__":
    run_bot()
