import datetime
import os
import requests
import time
import random

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from twilio.rest import Client

# ================= CONFIG =================
SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = 'primary'

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

# ================= RETRY SYSTEM =================
def safe_execute(func, max_retry=5):
    for attempt in range(max_retry):
        try:
            return func()
        except Exception as e:
            print(f"⚠️ Error: {e}")

            wait = (2 ** attempt) + random.uniform(0, 1)
            print(f"⏳ Retry {attempt+1}/{max_retry} dalam {round(wait,2)} detik...")
            time.sleep(wait)

    print("❌ Gagal setelah retry")
    return None

# ================= DATA HIJRIAH =================
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

# ================= HIJRIAH =================
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

    if not existing:
        print("⚠️ Skip (API error)")
        return

    if existing.get('items'):
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

    # delay random biar tidak kena limit
    time.sleep(random.uniform(0.2, 0.4))

# ================= CLEAN LEGACY =================
def clean_legacy_events():
    print("🧹 Hapus event lama (Senin/Kamis)...")

    now = datetime.datetime.utcnow().isoformat() + 'Z'

    events = safe_execute(lambda: service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=now,
        maxResults=2500,
        singleEvents=True
    ).execute())

    if not events:
        return

    deleted = 0

    for event in events.get('items', []):
        title = event.get('summary', '')

        if title == "Puasa Senin/Kamis":
            safe_execute(lambda: service.events().delete(
                calendarId=CALENDAR_ID,
                eventId=event['id']
            ).execute())
            deleted += 1

    print(f"🗑️ Dihapus legacy: {deleted}")
# clean_legacy_events()

# ================= MAIN =================
print("🚀 Update mulai...")

# ⚠️ Aktifkan hanya 1x kalau mau bersihin
# clean_legacy_events()

today = datetime.date.today()

for i in range(60):
    date = today + datetime.timedelta(days=i)
    h_day = get_hijri_day(date)
    h_month = get_hijri_month(date)

    if date.weekday() == 0:
        create_event(date, "Puasa Senin", COLOR["senin_kamis"])

    if date.weekday() == 3:
        create_event(date, "Puasa Kamis", COLOR["senin_kamis"])

    if h_day in [13, 14, 15]:
        create_event(date, "Puasa Ayyamul Bidh", COLOR["ayyamul_bidh"])

    if h_month == 6 and h_day == 9:
        create_event(date, "Puasa Arafah", COLOR["arafah"])

    if h_month == 7 and h_day == 10:
        create_event(date, "Puasa Asyura", COLOR["asyura"])

    if h_month == 2 and h_day == 15:
        create_event(date, "Nisfu Sya'ban", COLOR["nisfu"])

print("✅ Done!")
def write_log(status, info):
    with open("log.txt", "a") as f:
        f.write(f"{datetime.datetime.now()} | {status} | {info}\n")
write_log("INFO", "Script jalan")
write_log("WA", f"Kirim ke {num}")
write_log("ERROR", str(e))
