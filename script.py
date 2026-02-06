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

def send_professional_email(subject, title, subtitle, task_status, status_color):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = f"Superior LMS Assistant <{EMAIL_USER}>"
    msg['To'] = EMAIL_USER
    html_content = f"""
    <html>
    <body style='font-family: Arial, sans-serif; background-color: #f4f7f6; padding: 20px;'>
        <div style='max-width: 600px; margin: auto; background: white; border-radius: 12px; border: 1px solid #ddd; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1);'>
            <div style='background: {status_color}; color: white; padding: 25px; text-align: center;'>
                <h2 style='margin: 0;'>{title}</h2>
                <p style='margin: 5px 0 0; opacity: 0.9;'>{subtitle}</p>
            </div>
            <div style='padding: 25px;'>
                <p>Asalam-o-Alaikum Asim,</p>
                <p style='font-size: 16px; color: #333; line-height: 1.5;'>{task_status}</p>
                <div style='text-align: center; margin-top: 25px;'>
                    <a href='https://lms.superior.edu.pk/my/' style='background: {status_color}; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;'>Open LMS Dashboard</a>
                </div>
            </div>
            <div style='background: #f9f9f9; padding: 15px; text-align: center; font-size: 12px; color: #888; border-top: 1px solid #eee;'>
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

def run_bot():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        now_pak = datetime.utcnow() + timedelta(hours=5)
        current_hour = now_pak.hour
        
        # Dates to find on page
        today = [now_pak.strftime("%-d %B"), now_pak.strftime("%d %B")]
        tomorrow = [(now_pak + timedelta(days=1)).strftime("%-d %B"), (now_pak + timedelta(days=1)).strftime("%d %B")]
        two_days = [(now_pak + timedelta(days=2)).strftime("%-d %B"), (now_pak + timedelta(days=2)).strftime("%d %B")]

        try:
            page.goto("https://lms.superior.edu.pk/login/index.php")
            page.fill('input[name="username"]', LMS_USER)
            page.fill('input[name="password"]', LMS_PASS)
            page.keyboard.press("Enter")
            page.wait_for_timeout(15000) # Wait for dashboard to load

            # Poore page ka text uthao
            content = page.content()
            
            has_urgent = "Today" in content or any(d in content for d in today)
            has_tomorrow = any(d in content for d in tomorrow)
            has_upcoming = any(d in content for d in two_days)

            # --- RULES ---
            if 9 <= current_hour <= 11:
                if has_urgent:
                    send_professional_email("LMS Alert: Due Today!", "Task Due Today", "Action Required!", "⚠️ Aapka koi task aaj khatam ho raha hai. Please foran check karke submit karein.", "#d32f2f")
                else:
                    send_professional_email("LMS Status: All Clear ✅", "No Tasks Today", "Good Morning!", "✅ Aaj ki date mein koi deadline nahi mili. Relax and have a great day!", "#2e7d32")

            elif 16 <= current_hour <= 18:
                if has_urgent:
                    send_professional_email("LMS Evening Alert", "Submit Tonight!", "Urgent Reminder", "⚠️ Reminder: Aaj ki deadline wala task rehta hai. Aaj raat tak upload kar dein.", "#f57c00")
                elif has_tomorrow:
                    send_professional_email("LMS Alert: Due Tomorrow!", "Deadline Tomorrow", "1 Day Left", f"⚠️ Heads up! Aapka task kal due hai. Taiyari shuru kar dein!", "#673ab7")
                elif has_upcoming:
                    send_professional_email("LMS Alert: 2 Days Left", "Upcoming Deadline", "Due in 2 Days", f"⏳ Note: Aapka ek task 2 din baad due hai. Isey waqt par mukammal karlein.", "#1976d2")
                else:
                    send_professional_email("LMS Evening Status ✅", "All Clear", "No Urgent Deadlines", "✅ Bot ne check kiya hai, filhal koi urgent ya 2-din wali deadline nahi mili.", "#2e7d32")

            elif current_hour >= 21 and has_urgent:
                send_professional_email("LMS FINAL WARNING! 🚨", "Closing Soon!", "Last Chance", "🚨 Deadline khatam honay wali hai. Agar task upload nahi kiya to foran kar dein!", "#000000")

        except Exception as e:
            print(f"Error: {e}")
        browser.close()

if __name__ == "__main__":
    run_bot()
