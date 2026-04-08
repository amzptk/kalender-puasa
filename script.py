import datetime
import os
import requests
import time

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from twilio.rest import Client

# ===== CONFIG =====
SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = 'primary'
LOG_FILE = "sent_log.txt"

# ===== DATA HIJRIAH =====
hijri_month_start = {
    "2026-03-21": 4,
    "2026-04-19": 5,
    "2026-05-18": 6,
    "2026-06-17": 7,
    "2026-07-16": 8,
    "2026-08-15": 9,
    "2026-09-13": 10,
    "2026-10-13": 11,
    "2026-11-11": 12,
    "2026-12-11": 1,
    "2027-01-09": 2,
    "2027-02-08": 3,
    "2027-03-10": 4,
}

# ===== AUTH =====
creds = Credentials.from_authorized_user_file('token.json', SCOPES)
service = build('calendar', 'v3', credentials=creds)

# ===== WHATSAPP =====
def send_whatsapp(message):
    client = Client(
        os.getenv("TWILIO_SID"),
        os.getenv("TWILIO_TOKEN")
    )
    client.messages.create(
        from_='whatsapp:+14155238886',
        body=message,
        to='whatsapp:+6281347084840'
    )

# ===== FORMAT =====
def format_message(title, tipe):
    if tipe == "malam":
        return f"""🌙 Reminder Puasa Besok

Besok:
{title}

Jangan lupa sahur ya 😊"""
    else:
        return f"""🌄 Waktu Sahur

Hari ini:
{title}

Semangat puasa 💪"""

# ===== HIJRIAH =====
def get_hijri_day(date):
    for start_str in sorted(hijri_month_start.keys(), reverse=True):
        start_date = datetime.datetime.strptime(start_str, "%Y-%m-%d").date()
        if date >= start_date:
            return (date - start_date).days + 1
    return None

def get_hijri_month(date):
    for start_str, month in sorted(hijri_month_start.items(), reverse=True):
        start_date = datetime.datetime.strptime(start_str, "%Y-%m-%d").date()
        if date >= start_date:
            return month
    return None

# ===== IMSAK =====
def get_imsak_time(date):
    url = f"http://api.aladhan.com/v1/timingsByCity?city=Pontianak&country=Indonesia&method=2&date={date.strftime('%d-%m-%Y')}"
    res = requests.get(url).json()
    fajr = res['data']['timings']['Fajr']
    h, m = map(int, fajr.split(":"))
    return datetime.datetime.combine(date, datetime.time(h, m))

# ===== LOG =====
def already_sent(key):
    if not os.path.exists(LOG_FILE):
        return False
    with open(LOG_FILE, "r") as f:
        return key in f.read()

def mark_sent(key):
    with open(LOG_FILE, "a") as f:
        f.write(key + "\n")

# ===== CREATE EVENT =====
created = set()

def create_event(date, title):
    key = (date, title)
    if key in created:
        return
    created.add(key)

    event = {
        'summary': title,
        'start': {'date': date.isoformat()},
        'end': {'date': (date + datetime.timedelta(days=1)).isoformat()},
    }

    service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
    time.sleep(0.1)  # anti rate limit

# ===== PUASA BESOK =====
def get_tomorrow_fasting(date):
    next_day = date + datetime.timedelta(days=1)

    hijri_day = get_hijri_day(next_day)
    hijri_month = get_hijri_month(next_day)

    events = []

    if next_day.weekday() in [0, 3]:
        events.append("Puasa Senin/Kamis")

    if hijri_day in [13, 14, 15]:
        events.append("Puasa Ayyamul Bidh")

    if hijri_month == 6 and hijri_day == 9:
        events.append("Puasa Arafah")

    if hijri_month == 7 and hijri_day == 10:
        events.append("Puasa Asyura")

    return events

# ===== MAIN =====
print("🚀 Update mulai...")

today = datetime.date.today()

# 🔥 hanya generate 60 hari (hemat API)
for i in range(60):
    date = today + datetime.timedelta(days=i)

    hijri_day = get_hijri_day(date)
    hijri_month = get_hijri_month(date)

    if date.weekday() in [0, 3]:
        create_event(date, "Puasa Senin/Kamis")

    if hijri_day in [13, 14, 15]:
        create_event(date, "Puasa Ayyamul Bidh")

    if hijri_month == 6 and hijri_day == 9:
        create_event(date, "Puasa Arafah")

    if hijri_month == 7 and hijri_day == 10:
        create_event(date, "Puasa Asyura")

# ===== WHATSAPP =====
now = datetime.datetime.now()
events = get_tomorrow_fasting(today)

if events:
    text = "\n".join(events)

    # malam
    key1 = f"{today}-malam"
    if now.hour == 21 and not already_sent(key1):
        send_whatsapp(format_message(text, "malam"))
        mark_sent(key1)

    # sahur real
    imsak = get_imsak_time(today)
    sahur = imsak - datetime.timedelta(minutes=30)

    key2 = f"{today}-sahur"

    if abs((now - sahur).total_seconds()) < 600:
        if not already_sent(key2):
            send_whatsapp(format_message(text, "sahur"))
            mark_sent(key2)

print("✅ Done!")
