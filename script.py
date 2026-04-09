# ================= CLEAN (JALANKAN SEKALI SAJA) =================
def clean_old_events():
    print("🧹 Bersihkan event lama...")

    now = datetime.datetime.utcnow().isoformat() + 'Z'

    events = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=now,
        maxResults=2500,
        singleEvents=True
    ).execute()

    deleted = 0

    for event in events.get('items', []):
        summary = event.get('summary', '')

        if "Puasa" in summary:
            try:
                service.events().delete(
                    calendarId=CALENDAR_ID,
                    eventId=event['id']
                ).execute()
                deleted += 1
            except:
                pass

    print(f"🗑️ Dihapus: {deleted}")


# ================= MAIN =================
print("🚀 Update mulai...")

today = datetime.date.today()

# ⚠️ JALANKAN SEKALI SAJA LALU HAPUS
# clean_old_events()

# generate 60 hari
for i in range(60):
    date = today + datetime.timedelta(days=i)
    h_day = get_hijri_day(date)
    h_month = get_hijri_month(date)

    # ✅ FIX (tidak pakai Senin/Kamis gabungan lagi)
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
