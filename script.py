import datetime
import os
import requests
import time

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from twilio.rest import Client

# ===== CONFIG =====
SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = 'primary'
LOG_FILE = "sent_log.txt"

# ===== AUTH GOOGLE =====
creds = Credentials.from_authorized_user_file('token.json', SCOPES)
service = build('calendar', 'v3', credentials=creds)

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

# ===== WHATSAPP =====
def send_whatsapp(message):
    client = Client(
        os.getenv("TWILIO_SID"),
        os.getenv("TWILIO_TOKEN")
    )

    numbers = [
        "whatsapp:+6281347084840",  # ganti nomor kamu
        # tambah nomor lain di sini
    ]

    for number in numbers:
        try:
            msg = client.messages.create(
                from_='whatsapp:+14155238886',
                body=message,
                to=number
            )
            print("WA SENT:", number, msg.sid)
        except Exception as e:
            print("WA ERROR:", number, e)

# ===== FORMAT =====
def format_message(title, tipe):
    if tipe == "malam":
        return f"""🌙 *Reminder Puasa Besok*

{title}

Jangan lupa sahur 😊"""
    else:
        return f"""🌄 *Waktu Sahur*

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
    url = f"http://api.aladhan.com/v1/timingsByCity?city=Pontianak&country=Indonesia&date={date.strftime('%d-%m-%Y')}"
    res = requests.get(url).json()
    fajr = res['data']['timings']['Fajr']
    h, m = map(int, fajr.split(":"))
    return datetime.datetime.combine(date, datetime.time(h, m))

# ===== ANTI DOUBLE WA =====
def already_sent(key):
    if not os.path.exists(LOG_FILE):
        return False
    with open(LOG_FILE, "r") as f:
        return key in f.read()

def mark_sent(key):
    with open(LOG_FILE, "a") as f:
        f.write(key + "\n")

# ===== CREATE EVENT ANTI DUPLIKAT =====
def create_event(date, title):
    unique_id = f"{title}-{date.isoformat()}"

    events = service.events().list(
        calendarId=CALENDAR_ID,
        privateExtendedProperty=f"uid={unique_id}"
    ).execute()

    if events.get('items'):
        return

    event = {
        'summary': title,
        'start': {'date': date.isoformat()},
        'end': {'date': (date + datetime.timedelta(days=1)).isoformat()},
        'extendedProperties': {
            'private': {
                'uid': unique_id
            }
        }
    }

    service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
    time.sleep(0.1)

# ===== CEK PUASA =====
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

    if hijri_month == 2 and hijri_day == 15:
        events.append("Nisfu Sya'ban")

    return events

# ===== MAIN =====
print("🚀 Update mulai...")

today = datetime.date.today()

# hanya 60 hari (hemat API)
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

    if hijri_month == 2 and hijri_day == 15:
        create_event(date, "Nisfu Sya'ban")

# ===== WHATSAPP =====
now = datetime.datetime.now()
events = get_tomorrow_fasting(today)

if events:
    text = "\n".join(events)

    # ===== MALAM (WINDOW) =====
    key1 = f"{today}-malam"

    if now.hour == 21 and now.minute < 10:
        if not already_sent(key1):
            send_whatsapp(format_message(text, "malam"))
            mark_sent(key1)

    # ===== SAHUR =====
    imsak = get_imsak_time(today)
    sahur = imsak - datetime.timedelta(minutes=30)

    key2 = f"{today}-sahur"

    if abs((now - sahur).total_seconds()) < 600:
        if not already_sent(key2):
            send_whatsapp(format_message(text, "sahur"))
            mark_sent(key2)

print("✅ Done!")
