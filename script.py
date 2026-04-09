import datetime
import os
import requests
import time
import random

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from twilio.rest import Client

# ================= LOG =================
def write_log(status, info):
    with open("log.txt", "a", encoding="utf-8") as f:
        waktu = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"{waktu} | {status} | {info}\n")

# ================= CONFIG =================
SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = 'primary'

# WA PERSONAL
NUMBERS = {
    "Abi": "whatsapp:+6281347084840",
    "Ummi Tersayang": "whatsapp:+6285292772632"
}

# ================= AUTH =================
creds = Credentials.from_authorized_user_file('token.json', SCOPES)
service = build('calendar', 'v3', credentials=creds)

# ================= WARNA =================
COLOR = {
    "senin_kamis": "1",
    "ayyamul_bidh": "2",
    "arafah": "11",
    "asyura": "3",
    "nisfu": "5"
}

# ================= RETRY =================
def safe_execute(func, max_retry=5):
    for attempt in range(max_retry):
        try:
            return func()
        except Exception as e:
            print("⚠️ Error:", e)
            write_log("ERROR", str(e))
            time.sleep((2 ** attempt) + random.random())
    return None

# ================= WA =================
def send_wa_personal(name, number, message):
    client = Client(
        os.getenv("TWILIO_SID"),
        os.getenv("TWILIO_TOKEN")
    )

    try:
        client.messages.create(
            from_='whatsapp:+14155238886',
            body=message,
            to=number
        )
        print(f"WA sent ke {name}")
        write_log("WA", f"{name} -> {number}")
    except Exception as e:
        print("WA error:", e)
        write_log("ERROR", str(e))

def format_message(name, title):
    return f"""🕌 *PENGINGAT PUASA*

Halo {name} 😊

📅 Besok ada: {title}

🤲 Jangan lupa niat & sahur ya"""

# ================= HIJRIAH =================
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

def get_hijri_day(date):
    for start_str in sorted(hijri_month_start.keys(), reverse=True):
        start = datetime.datetime.strptime(start_str, "%Y-%m-%d").date()
        if date >= start:
            return (date - start).days + 1
    return None

def get_hijri_month(date):
    for start_str, month in sorted(hijri_month_start.items(), reverse=True):
        start = datetime.datetime.strptime(start_str, "%Y-%m-%d").date()
        if date >= start:
            return month
    return None

# ================= CREATE EVENT =================
def create_event(date, title, color):
    uid = f"{title}-{date.isoformat()}"

    existing = safe_execute(lambda: service.events().list(
        calendarId=CALENDAR_ID,
        privateExtendedProperty=f"uid={uid}"
    ).execute())

    if not existing or existing.get('items'):
        return

    event = {
        'summary': title,
        'start': {'date': date.isoformat()},
        'end': {'date': (date + datetime.timedelta(days=1)).isoformat()},
        'colorId': color,
        'extendedProperties': {'private': {'uid': uid}}
    }

    safe_execute(lambda: service.events().insert(
        calendarId=CALENDAR_ID,
        body=event
    ).execute())

    write_log("EVENT", f"{title} - {date}")
    time.sleep(random.uniform(0.2, 0.4))

# ================= MAIN =================
print("🚀 Update mulai...")
write_log("INFO", "Script jalan")

today = datetime.date.today()

for i in range(60):
    date = today + datetime.timedelta(days=i)
    h_day = get_hijri_day(date)
    h_month = get_hijri_month(date)

    events = []

    if date.weekday() == 0:
        events.append("Puasa Senin")
        create_event(date, "Puasa Senin", COLOR["senin_kamis"])

    if date.weekday() == 3:
        events.append("Puasa Kamis")
        create_event(date, "Puasa Kamis", COLOR["senin_kamis"])

    if h_day in [13, 14, 15]:
        events.append("Puasa Ayyamul Bidh")
        create_event(date, "Puasa Ayyamul Bidh", COLOR["ayyamul_bidh"])

    if h_month == 6 and h_day == 9:
        events.append("Puasa Arafah")
        create_event(date, "Puasa Arafah", COLOR["arafah"])

    # ===== WA BESOK =====
    if i == 1 and events:
        text = ", ".join(events)

        for name, number in NUMBERS.items():
            send_wa_personal(name, number, format_message(name, text))

print("✅ Done!")
write_log("INFO", "Script selesai")
