import datetime
import os
import random
from zoneinfo import ZoneInfo
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# Set your location here
CITY = os.environ.get("CITY", "Guelma")
COUNTRY = os.environ.get("COUNTRY", "Algeria")
METHOD = 19  # 19 = Algerian Ministry of Religious Affairs (or 3 = Muslim World League)

PRAYERS = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]

MORNING_AZKAR = (
    "🌅 *Morning Azkar (أذكار الصباح)*\n\n"
    "1️⃣ *Ayat al-Kursi* (Recite once)\n"
    "اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ...\n\n"
    "2️⃣ *Sayyidul Istighfar:*\n"
    "اللَّهُمَّ أَنْتَ رَبِّي لَا إِلَهَ إِلَّا أَنْتَ، خَلَقْتَنِي وَأَنَا عَبْدُكَ، وَأَنَا عَلَى عَهْدِكَ وَوَعْدِكَ مَا اسْتَطَعْتُ...\n\n"
    "3️⃣ *Tasbih (3 times):*\n"
    "سُبْحَانَ اللَّهِ وَبِحَمْدِهِ: عَدَدَ خَلْقِهِ، وَرِضَا نَفْسِهِ، وَزِنَةَ عَرْشِهِ، وَمِدَادَ كَلِمَاتِهِ"
)

EVENING_AZKAR = (
    "🌇 *Evening Azkar (أذكار المساء)*\n\n"
    "1️⃣ *Ayat al-Kursi & Last 2 Verses of Surah Al-Baqarah*\n\n"
    "2️⃣ *Evening Remembrance:*\n"
    "أَمْسَيْنَا وَأَمْسَى الْمُلْكُ لِلَّهِ، وَالْحَمْدُ لِلَّهِ لَا إِلَهَ إِلَّا اللهُ وَحْدَهُ لَا شَرِيكَ لَهُ\n\n"
    "3️⃣ *Protection Dua (3 times):*\n"
    "بِسْمِ اللهِ الَّذِي لَا يَضُرُّ مَعَ اسْمِهِ شَيْءٌ فِي الْأَرْضِ وَلَا فِي السَّمَاءِ وَهُوَ السَّمِيعُ الْعَلِيمُ"
)

DAILY_DUAS = [
    "🤲 *Dua of the Day:*\nرَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ",
    "🤲 *Dua of the Day:*\nيَا مُقَلِّبَ الْقُلُوبِ ثَبِّتْ قَلْبِي عَلَى دِينِكَ",
    "🤲 *Dua of the Day:*\nلَا إِلَهَ إِلَّا أَنْتَ سُبْحَانَكَ إِنِّي كُنْتُ مِنَ الظَّالِمِينَ",
    "🤲 *Dua of the Day:*\nاللَّهُمَّ إِنِّي أَسْأَلُكَ عِلْمًا نَافِعًا، وَرِزْقًا طَيِّبًا، وَعَمَلًا مُتَقَبَّلًا",
]


def send_telegram_message(text: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload, timeout=10)


def is_within_window(target_dt: datetime.datetime, now_dt: datetime.datetime, window_minutes: int = 15) -> bool:
    """Returns True if target_dt occurred within the last `window_minutes`."""
    diff_seconds = (now_dt - target_dt).total_seconds()
    return 0 <= diff_seconds < (window_minutes * 60)


def main():
    url = "https://api.aladhan.com/v1/timingsByCity"
    params = {"city": CITY, "country": COUNTRY, "method": METHOD}
    res = requests.get(url, params=params, timeout=10).json()
    if res.get("code") != 200:
        print("Failed to fetch prayer times")
        return

    data = res["data"]
    timings = data["timings"]
    tz = ZoneInfo(data["meta"]["timezone"])
    now = datetime.datetime.now(tz)

    # If triggered manually from GitHub Actions button, send a test confirmation + today's schedule
    if os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch":
        schedule_lines = "\n".join([f"• *{p}:* {timings[p]}" for p in PRAYERS])
        send_telegram_message(
            f"✅ *Bot Connected Successfully!*\n"
            f"📍 *Location:* {CITY}, {COUNTRY}\n\n"
            f"🕌 *Today's Prayer Times:*\n{schedule_lines}\n\n"
            f"---\n{random.choice(DAILY_DUAS)}"
        )
        return

    for prayer in PRAYERS:
        raw_time = timings[prayer].split(" ")[0]
        hour, minute = map(int, raw_time.split(":"))
        prayer_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # 1. Check Salah time
        if is_within_window(prayer_dt, now):
            send_telegram_message(
                f"🕌 *It is time for {prayer} prayer ({raw_time}).*\n\n"
                f"📿 _After-Prayer Sunnah:_ Astaghfirullah (3x), Ayat al-Kursi, "
                f"SubhanAllah (33x), Alhamdulillah (33x), Allahu Akbar (34x)."
            )

        # 2. Morning Azkar (30 mins after Fajr)
        if prayer == "Fajr":
            morning_dt = prayer_dt + datetime.timedelta(minutes=30)
            if is_within_window(morning_dt, now):
                send_telegram_message(f"{MORNING_AZKAR}\n\n---\n{random.choice(DAILY_DUAS)}")

        # 3. Evening Azkar (30 mins after Asr)
        if prayer == "Asr":
            evening_dt = prayer_dt + datetime.timedelta(minutes=30)
            if is_within_window(evening_dt, now):
                send_telegram_message(f"{EVENING_AZKAR}\n\n---\n{random.choice(DAILY_DUAS)}")


if __name__ == "__main__":
    main()
