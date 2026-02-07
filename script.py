import os
import smtplib
from playwright.sync_api import sync_playwright
from email.message import EmailMessage
from datetime import datetime, timedelta

# Credentials from Secrets
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
    html_content = f"<html><body style='font-family: Arial, sans-serif; background-color: #f4f7f6; padding: 20px;'><div style='max-width: 600px; margin: auto; background: white; border-radius: 12px; border: 1px solid #ddd; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1);'><div style='background: {status_color}; color: white; padding: 25px; text-align: center;'><h2 style='margin: 0;'>{title}</h2><p style='margin: 5px 0 0; opacity: 0.9;'>{subtitle}</p></div><div style='padding: 25px;'><p>Asalam-o-Alaikum Asim,</p><p style='font-size: 15px;'>Here is your LMS report:</p>{task_html}</div><div style='background: #f9f9f9; padding: 15px; text-align: center; font-size: 12px; color: #888;'>Superior Automated Assistant</div></div></body></html>"
    msg.add_alternative(html_content, subtype='html')
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_USER, EMAIL_PASS)
        smtp.send_message(msg)

def scrape_day_tasks(page, url):
    tasks = []
    try:
        print(f"Navigating to: {url}")
        page.goto(url, wait_until="load", timeout=90000)
        page.wait_for_timeout(7000)
        event_elements = page.query_selector_all('.event')
        for event in event_elements:
            full_text = event.inner_text()
            if "Add submission" not in full_text: continue
            name = event.query_selector('h3').inner_text().strip()
            course = "LMS Course"
            course_el = event.query_selector('.course') or event.query_selector('a[href*="course/view.php"]')
            if course_el: course = course_el.inner_text().strip()
            tasks.append({'name': name, 'course': course, 'date': full_info.replace("Add submission", "").strip() if 'full_info' in locals() else full_text})
    except Exception as e:
        print(f"Error scraping {url}: {e}")
    return tasks

def run_bot():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Global timeout set to 60 seconds
        context = browser.new_context()
        context.set_default_timeout(60000)
        page = context.new_page()
        
        now_pak = datetime.utcnow() + timedelta(hours=5)
        current_hour = now_pak.hour
        today_ts = int(now_pak.timestamp())
        tomorrow_ts = int((now_pak + timedelta(days=1)).timestamp())
        two_days_ts = int((now_pak + timedelta(days=2)).timestamp())

        try:
            print(f"LMS Check started at {now_pak.strftime('%H:%M')}...")
            page.goto("https://lms.superior.edu.pk/login/index.php", timeout=90000)
            page.fill('input[name="username"]', LMS_USER)
            page.fill('input[name="password"]', LMS_PASS)
            page.keyboard.press("Enter")
            page.wait_for_load_state("networkidle")
            print("Login successful.")

            tasks_today = scrape_day_tasks(page, f"https://lms.superior.edu.pk/calendar/view.php?view=day&time={today_ts}")
            tasks_tomorrow = scrape_day_tasks(page, f"https://lms.superior.edu.pk/calendar/view.php?view=day&time={tomorrow_ts}")
            tasks_upcoming = scrape_day_tasks(page, f"https://lms.superior.edu.pk/calendar/view.php?view=day&time={two_days_ts}")

            # --- RULES ---
            if 8 <= current_hour <= 12: # Morning (8 AM to 12 PM)
                if tasks_today: send_professional_email("LMS Alert: Due Today!", "Tasks Due Today", "Ending tonight!", tasks_today, "#d32f2f")
                else: send_professional_email("LMS Status: All Clear ✅", "Good Morning!", "No tasks for today.", [], "#2e7d32")

            elif 16 <= current_hour <= 20: # Evening (4 PM to 8 PM)
                if tasks_today: send_professional_email("LMS Evening Reminder", "Still Pending!", "Submit tonight!", tasks_today, "#f57c00")
                elif tasks_tomorrow: send_professional_email("LMS Alert: Due Tomorrow!", "Deadline Tomorrow", "1 day left.", tasks_tomorrow, "#673ab7")
                elif tasks_upcoming: send_professional_email("LMS Alert: 2 Days Left", "Upcoming Deadline", "Due in 2 days.", tasks_upcoming, "#0277bd")
                else: send_professional_email("LMS Evening Status ✅", "All Clear", "No urgent tasks.", [], "#2e7d32")

            elif current_hour >= 21 and tasks_today: # Night
                send_professional_email("LMS FINAL WARNING! 🚨", "Closing Soon!", "Last chance!", tasks_today, "#000000")

        except Exception as e:
            print(f"Main execution error: {e}")
        
        browser.close()

if __name__ == "__main__":
    run_bot()
