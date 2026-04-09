import datetime
import time
import requests
import os
import random

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from twilio.rest import Client

# ================= CONFIG =================
SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = 'primary'

CITY = "Pontianak"
COUNTRY = "Indonesia"

TWILIO_FROM = 'whatsapp:+14155238886'
NUMBERS = [
    "whatsapp:+6281347084840"
]

# ================= AUTH =================
creds = Credentials.from_authorized_user_file('token.json', SCOPES)
service = build('calendar', 'v3', credentials=creds)

# ================= RETRY SYSTEM =================
def safe_execute(func, retry=5):
    for i in range(retry):
        try:
            return func()
        except Exception as e:
            wait = (2 ** i) + random.random()
            print("⚠️ Retry:", wait, e)
            time.sleep(wait)
    return None

# ================= FORMAT PESAN =================
def format_message(name):
    doa = {
        "Subuh": "Ya Allah, berkahi kami di pagi hari 🌅",
        "Dzuhur": "Jangan tinggalkan sholat di tengah kesibukan 🏢",
        "Ashar": "Jangan sampai lalai menjelang sore 🌇",
        "Maghrib": "Waktu berbuka dan bersyukur 🍽️",
        "Isya": "Penutup hari dengan ibadah 🌙"
    }

    return f"""🕌 *WAKTU SHOLAT {name.upper()}*

⏰ 10 menit lagi masuk waktu sholat {name} di Pontianak

📿 {doa.get(name, "")}

📖 "Sesungguhnya sholat itu adalah kewajiban yang ditentukan waktunya"
(QS. An-Nisa: 103)

🤲 Yuk segera bersiap 😊"""

# ================= WHATSAPP =================
def send_wa(message):
    client = Client(
        os.getenv("TWILIO_SID"),
        os.getenv("TWILIO_TOKEN")
    )

    for num in NUMBERS:
        try:
            client.messages.create(
                from_=TWILIO_FROM,
                body=message,
                to=num
            )
            print("WA sent:", num)
        except Exception as e:
            print("WA error:", e)

# ================= GET JADWAL =================
def get_prayer_times(date):
    url = f"http://api.aladhan.com/v1/timingsByCity?city={CITY}&country={COUNTRY}&date={date.strftime('%d-%m-%Y')}"
    res = requests.get(url).json()
    return res['data']['timings']

# ================= CREATE EVENT =================
def create_event(date, name, time_str):
    uid = f"{name}-{date}"

    existing = safe_execute(lambda: service.events().list(
        calendarId=CALENDAR_ID,
        privateExtendedProperty=f"uid={uid}"
    ).execute())

    if not existing:
        return

    if existing.get('items'):
        return

    hour, minute = map(int, time_str.split(":"))
    start = datetime.datetime.combine(date, datetime.time(hour, minute))

    event = {
        'summary': f"Sholat {name}",
        'start': {'dateTime': start.isoformat(), 'timeZone': 'Asia/Jakarta'},
        'end': {'dateTime': (start + datetime.timedelta(minutes=10)).isoformat(), 'timeZone': 'Asia/Jakarta'},
        'extendedProperties': {'private': {'uid': uid}}
    }

    safe_execute(lambda: service.events().insert(
        calendarId=CALENDAR_ID,
        body=event
    ).execute())

    time.sleep(random.uniform(0.2, 0.4))

# ================= MAIN =================
print("🚀 Update sholat...")

today = datetime.date.today()
now = datetime.datetime.now()

times = get_prayer_times(today)

jadwal = {
    "Subuh": times["Fajr"],
    "Dzuhur": times["Dhuhr"],
    "Ashar": times["Asr"],
    "Maghrib": times["Maghrib"],
    "Isya": times["Isha"]
}

# ===== CREATE CALENDAR =====
for name, t in jadwal.items():
    create_event(today, name, t)

# ===== WA REMINDER =====
for name, t in jadwal.items():
    hour, minute = map(int, t.split(":"))
    waktu = datetime.datetime.combine(today, datetime.time(hour, minute))
    reminder = waktu - datetime.timedelta(minutes=10)

    # if abs((now - reminder).total_seconds()) < 300:
        send_wa(format_message(name))

print("✅ Done!")
