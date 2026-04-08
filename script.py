import datetime
import os

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from twilio.rest import Client

# ===== CONFIG =====
SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = 'primary'

# ===== DATA HIJRIAH (ACUAN ISBAT) =====
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

# ===== AUTH GOOGLE =====
creds = None
if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
else:
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    with open('token.json', 'w') as token:
        token.write(creds.to_json())

service = build('calendar', 'v3', credentials=creds)

# ===== TWILIO =====
def send_whatsapp(message):
    client = Client(
        os.getenv("TWILIO_SID"),
        os.getenv("TWILIO_TOKEN")
    )

    client.messages.create(
        from_='whatsapp:+14155238886',
        body=message,
        to='whatsapp:+6281347084840'  # GANTI NOMOR KAMU
    )

# ===== FORMAT PESAN =====
def format_message(title, tipe):
    if tipe == "malam":
        return f"""🌙 *Reminder Puasa Besok*

Assalamu’alaikum 😊

Besok insyaAllah:
📌 *{title}*

Yuk niat & siapkan sahur 🙏
Semoga Allah mudahkan ibadah kita 🤲
"""
    else:
        return f"""🌄 *Waktu Sahur*

Assalamu’alaikum 😊

Hari ini:
📌 *{title}*

Yuk sahur 🍽️
Semoga puasanya lancar & berkah 🤲
"""

# ===== FUNGSI HIJRIAH =====
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

# ===== HAPUS EVENT LAMA =====
def clear_old_events():
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    events = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=now,
        maxResults=2500,
        singleEvents=True
    ).execute()

    for event in events.get('items', []):
        if "Puasa" in event.get('summary', ''):
            service.events().delete(
                calendarId=CALENDAR_ID,
                eventId=event['id']
            ).execute()

# ===== CEK PUASA BESOK =====
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
print("🔄 Update kalender...")

clear_old_events()

start_date = datetime.date.today()

for i in range(365):
    date = start_date + datetime.timedelta(days=i)

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

# ===== WHATSAPP TRIGGER =====
now = datetime.datetime.now()
today = datetime.date.today()

events = get_tomorrow_fasting(today)

if events:
    text = "\n".join(events)

    # kirim malam
    if now.hour == 21:
        send_whatsapp(format_message(text, "malam"))

    # kirim sahur
    if now.hour == 3:
        send_whatsapp(format_message(text, "sahur"))

print("✅ Selesai semua!")
