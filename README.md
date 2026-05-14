# 🎓 Superior LMS Automation Bot

An intelligent, automated monitoring system designed to keep students on track with their academic deadlines. This bot scrapes the Superior University LMS, identifies pending assignments, and sends professional HTML email alerts based on urgency.

---

## 🚀 Key Features

- **Automated Scraper**  
  Uses Playwright to navigate the LMS and identify tasks specifically marked with **"Add submission."**

- **Smart Scheduling**  
  Fully integrated with GitHub Actions to run automatically at:
  - 🕙 10:00 AM  
  - 🕔 05:00 PM  
  - 🕚 11:00 PM (PKT)

- **Professional Alerts**  
  Sends beautifully formatted HTML emails with color-coded urgency:
  
  - 🟢 **Green** → No pending tasks  
  - 🔵 **Blue** → Upcoming deadlines (5 PM alert)  
  - 🔴 **Red** → Final warning (10 AM alert)  
  - ⚫ **Black** → Immediate action required (11 PM alert)

- **Serverless Execution**  
  Runs entirely on GitHub’s cloud infrastructure using CI/CD workflows.

---

## 🛠️ Tech Stack

- **Language:** Python 3.9+  
- **Automation:** Playwright (Chromium)  
- **CI/CD:** GitHub Actions  
- **Scheduling:** YAML Cron Jobs  
- **Emailing:** smtplib & EmailMessage  

---

## 📂 Project Structure

    .github/workflows/
    └── main.yml          # GitHub Actions configuration (Cron settings)
    script.py             # Main logic for scraping and emailing
    requirements.txt      # Python dependencies
    README.md             # Project documentation

---

## ⚙️ Setup & Installation

### 1. Local Setup

Clone the repository and install dependencies:

    git clone https://github.com/Asimsayam/lms-automation-bot.git
    cd lms-automation-bot
    pip install -r requirements.txt
    playwright install chromium --with-deps

---

## 🔐 Environment Variables

The bot requires the following secrets to function:

- **LMS_USER** → Your LMS registration number  
- **LMS_PASS** → Your LMS password  
- **EMAIL_USER** → Gmail address for sending alerts  
- **EMAIL_PASS** → Gmail App Password (not your regular password)  

---

## ⚙️ GitHub Actions Configuration

To run this automatically in the cloud:

1. Go to your GitHub repository settings  
2. Navigate to **Secrets and variables → Actions**  
3. Click on **New repository secret**  
4. Add all the environment variables listed above  

---

## ⏰ Cron Schedule (Pakistan Time)

The bot is configured to run at:

- 🕙 **10:00 AM** → Status check / Final warning for today  
- 🕔 **05:00 PM** → Upcoming deadline alerts  
- 🕚 **11:00 PM** → Last-minute emergency alert  

---

## 💡 How It Works

1. Bot logs into LMS using credentials  
2. Scrapes dashboard for assignments with "Add submission"  
3. Categorizes tasks based on urgency  
4. Generates HTML email with color-coded alerts  
5. Sends email via Gmail SMTP  
6. Runs automatically using GitHub Actions  

---

## 🔒 Security Note

- Never share your credentials publicly  
- Always use GitHub Secrets  
- Use Gmail App Password instead of your real password  

---

## 👨‍💻 Author

Developed with by **Asim Sayyam**
