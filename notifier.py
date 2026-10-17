import datetime
import json
import os
import random
from zoneinfo import ZoneInfo
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# Pre-configured for Guelma, Algeria (can be overridden in GitHub Secrets/Vars)
CITY = os.environ.get("CITY", "Guelma")
COUNTRY = os.environ.get("COUNTRY", "Algeria")
METHOD = 19  # 19 = Algerian Ministry of Religious Affairs and Wakfs

PRAYERS = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
STATE_FILE = ".sent_alerts.json"

# =====================================================================
# 1. COMPLETE HISNUL MUSLIM MORNING & EVENING AZKAR + SLEEP AZKAR
# =====================================================================

MORNING_AZKAR = (
    "🌅 <b>أذكار الصباح (Morning Azkar — Hisnul Muslim)</b>\n\n"
    "1️⃣ <b>آية الكرسي (مرة واحدة - 1x):</b>\n"
    "﴿اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ لَا تَأْخُذُهُ سِنَةٌ وَلَا نَوْمٌ لَّهُ مَا فِي السَّمَاوَاتِ وَمَا فِي الْأَرْضِ...﴾\n\n"
    "2️⃣ <b>المعوذات (3 مرات - 3x):</b>\n"
    "سورة الإخلاص، سورة الفلق، سورة الناس.\n\n"
    "3️⃣ <b>سيد الاستغفار (مرة واحدة - 1x):</b>\n"
    "«اللَّهُمَّ أَنْتَ رَبِّي لَا إِلَهَ إِلَّا أَنْتَ، خَلَقْتَنِي وَأَنَا عَبْدُكَ، وَأَنَا عَلَى عَهْدِكَ وَوَعْدِكَ مَا اسْتَطَعْتُ، أَعُوذُ بِكَ مِنْ شَرِّ مَا صَنَعْتُ، أَبُوءُ لَكَ بِنِعْمَتِكَ عَلَيَّ، وَأَبُوءُ بِذَنْبِي فَاغْفِرْ لِي فَإِنَّهُ لَا يَغْفِرُ الذُّنُوبَ إِلَّا أَنْتَ»\n\n"
    "4️⃣ <b>دعاء الصباح (مرة واحدة - 1x):</b>\n"
    "«أَصْبَحْنَا وَأَصْبَحَ الْمُلْكُ لِلَّهِ، وَالْحَمْدُ لِلَّهِ، لَا إِلَهَ إِلَّا اللهُ وَحْدَهُ لَا شَرِيكَ لَهُ، لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ»\n\n"
    "5️⃣ <b>الحفظ من الضر (3 مرات - 3x):</b>\n"
    "«بِسْمِ اللهِ الَّذِي لَا يَضُرُّ مَعَ اسْمِهِ شَيْءٌ فِي الْأَرْضِ وَلَا فِي السَّمَاءِ وَهُوَ السَّمِيعُ الْعَلِيمُ»\n\n"
    "6️⃣ <b>الرضى بالله (3 مرات - 3x):</b>\n"
    "«رَضِيتُ بِاللهِ رَبًّا، وَبِالْإِسْلَامِ دِينًا، وَبِمُحَمَّدٍ ﷺ نَبِيًّا»\n\n"
    "7️⃣ <b>كفاية الهم (7 مرات - 7x):</b>\n"
    "«حَسْبِيَ اللَّهُ لَا إِلَهَ إِلَّا هُوَ عَلَيْهِ تَوَكَّلْتُ وَهُوَ رَبُّ الْعَرْشِ الْعَظِيمِ»\n\n"
    "8️⃣ <b>التسبيح المضاعف (3 مرات - 3x):</b>\n"
    "«سُبْحَانَ اللَّهِ وَبِحَمْدِهِ: عَدَدَ خَلْقِهِ، وَرِضَا نَفْسِهِ، وَزِنَةَ عَرْشِهِ، وَمِدَادَ كَلِمَاتِهِ»\n\n"
    "9️⃣ <b>التسبيح والتهليل (100 مرة - 100x):</b>\n"
    "«سُبْحَانَ اللَّهِ وَبِحَمْدِهِ»"
)

EVENING_AZKAR = (
    "🌇 <b>أذكار المساء (Evening Azkar — Hisnul Muslim)</b>\n\n"
    "1️⃣ <b>آية الكرسي + آخر آيتين من سورة البقرة (مرة واحدة - 1x):</b>\n"
    "﴿آمَنَ الرَّسُولُ بِمَا أُنزِلَ إِلَيْهِ مِن رَّبِّهِ وَالْمُؤْمِنُونَ...﴾\n\n"
    "2️⃣ <b>المعوذات (3 مرات - 3x):</b>\n"
    "سورة الإخلاص، سورة الفلق، سورة الناس.\n\n"
    "3️⃣ <b>دعاء المساء (مرة واحدة - 1x):</b>\n"
    "«أَمْسَيْنَا وَأَمْسَى الْمُلْكُ لِلَّهِ، وَالْحَمْدُ لِلَّهِ، لَا إِلَهَ إِلَّا اللهُ وَحْدَهُ لَا شَرِيكَ لَهُ، لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ»\n\n"
    "4️⃣ <b>سيد الاستغفار (مرة واحدة - 1x):</b>\n"
    "«اللَّهُمَّ أَنْتَ رَبِّي لَا إِلَهَ إِلَّا أَنْتَ، خَلَقْتَنِي وَأَنَا عَبْدُكَ...»\n\n"
    "5️⃣ <b>الحفظ والتحصين (3 مرات - 3x):</b>\n"
    "«أَعُوذُ بِكَلِمَاتِ اللهِ التَّامَّاتِ مِنْ شَرِّ مَا خَلَقَ»\n"
    "«بِسْمِ اللهِ الَّذِي لَا يَضُرُّ مَعَ اسْمِهِ شَيْءٌ فِي الْأَرْضِ وَلَا فِي السَّمَاءِ وَهُوَ السَّمِيعُ الْعَلِيمُ»\n\n"
    "6️⃣ <b>كفاية الهم (7 مرات - 7x):</b>\n"
    "«حَسْبِيَ اللَّهُ لَا إِلَهَ إِلَّا هُوَ عَلَيْهِ تَوَكَّلْتُ وَهُوَ رَبُّ الْعَرْشِ الْعَظِيمِ»\n\n"
    "7️⃣ <b>الصلاة على النبي ﷺ (10 مرات - 10x):</b>\n"
    "«اللَّهُمَّ صَلِّ وَسَلِّمْ عَلَى نَبِيِّنَا مُحَمَّدٍ»"
)

SLEEP_AZKAR = (
    "🌙 <b>أذكار النوم وسورة الملك (Before Sleep Reminders)</b>\n\n"
    "📖 <b>سورة الملك (Surah Al-Mulk):</b>\n"
    "Don't forget to recite Surah Al-Mulk (30 verses) before sleeping — it intercedes for its reciter and protects from the punishment of the grave.\n\n"
    "🤲 <b>أذكار النوم (Sunnah Before Sleeping):</b>\n"
    "• Perform Wudu and dust your bed 3 times.\n"
    "• Cup your hands, recite <b>Al-Ikhlas, Al-Falaq, An-Nas</b>, blow into them, and wipe over your body (3x).\n"
    "• Recite <b>Ayat al-Kursi</b> and the last 2 verses of <b>Surah Al-Baqarah</b>.\n"
    "• <b>Tasbih Fatimi:</b> SubhanAllah (33x), Alhamdulillah (33x), Allahu Akbar (34x).\n"
    "• Say: «بِاسْمِكَ رَبِّي وَضَعْتُ جَنْبِي، وَبِكَ أَرْفَعُهُ...» and «بِاسْمِكَ اللَّهُمَّ أَمُوتُ وَأَحْيَا»."
)

DAILY_DUAS = [
    "🤲 <b>Dua of the Day:</b>\n«رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ»\n<i>(Our Lord, give us in this world that which is good and in the Hereafter that which is good, and protect us from the punishment of the Fire.)</i>",
    "🤲 <b>Dua of the Day:</b>\n«يَا مُقَلِّبَ الْقُلُوبِ ثَبِّتْ قَلْبِي عَلَى دِينِكَ»\n<i>(O Turner of the hearts, make my heart firm upon Your religion.)</i>",
    "🤲 <b>Dua of the Day:</b>\n«اللَّهُمَّ إِنِّي أَسْأَلُكَ الْهُدَى وَالتُّقَى وَالْعَفَافَ وَالْغِنَى»\n<i>(O Allah, I ask You for guidance, piety, chastity, and self-sufficiency.)</i>",
    "🤲 <b>Dua of the Day:</b>\n«اللَّهُمَّ إِنِّي أَسْأَلُكَ عِلْمًا نَافِعًا، وَرِزْقًا طَيِّبًا، وَعَمَلًا مُتَقَبَّلًا»\n<i>(O Allah, I ask You for beneficial knowledge, goodly provision, and acceptable deeds.)</i>",
    "🤲 <b>Dua of the Day:</b>\n«اللَّهُمَّ أَعِنِّي عَلَى ذِكْرِكَ، وَشُكْرِكَ، وَحُسْنِ عِبَادَتِكَ»\n<i>(O Allah, help me to remember You, to give thanks to You, and to worship You in the best manner.)</i>",
    "🤲 <b>Dua of the Day:</b>\n«لَا إِلَهَ إِلَّا أَنْتَ سُبْحَانَكَ إِنِّي كُنْتُ مِنَ الظَّالِمِينَ»\n<i>(There is no deity except You; exalted are You. Indeed, I have been of the wrongdoers.)</i>",
]

AUTHENTIC_HADITHS = [
    "📚 <b>Hadith of the Day:</b>\nقال رسول الله ﷺ: «كَلِمَتَانِ خَفِيفَتَانِ عَلَى اللِّسَانِ، ثَقِيلَتَانِ فِي الْمِيزَانِ، حَبِيبَتَانِ إِلَى الرَّحْمَنِ: سُبْحَانَ اللَّهِ وَبِحَمْدِهِ، سُبْحَانَ اللَّهِ الْعَظِيمِ»\n<i>(Two words are light on the tongue, weigh heavily in the balance, and are beloved to the Most Merciful: SubhanAllahi wa bihamdihi, SubhanAllahil-Adheem.) — Sahih Al-Bukhari & Muslim</i>",
    "📚 <b>Hadith of the Day:</b>\nقال رسول الله ﷺ: «مَنْ صَلَّى الْبَرْدَيْنِ دَخَلَ الْجَنَّةَ»\n<i>(Whoever prays the two cool prayers [Fajr and Asr] will enter Paradise.) — Sahih Al-Bukhari</i>",
    "📚 <b>Hadith of the Day:</b>\nقال رسول الله ﷺ: «أَحَبُّ الأَعْمَالِ إِلَى اللَّهِ أَدْوَمُهَا وَإِنْ قَلَّ»\n<i>(The most beloved of deeds to Allah are those that are most consistent, even if they are small.) — Sahih Muslim</i>",
    "📚 <b>Hadith of the Day:</b>\nقال رسول الله ﷺ: «مَنْ سَلَكَ طَرِيقًا يَلْتَمِسُ فِيهِ عِلْمًا سَهَّلَ اللَّهُ لَهُ بِهِ طَرِيقًا إِلَى الْجَنَّةِ»\n<i>(Whoever takes a path upon which to obtain knowledge, Allah makes the path to Paradise easy for him.) — Sahih Muslim</i>",
    "📚 <b>Hadith of the Day:</b>\nقال رسول الله ﷺ: «الدُّعَاءُ بَيْنَ الأَذَانِ وَالإِقَامَةِ لاَ يُرَدُّ»\n<i>(Supplication made between the Adhan and the Iqamah is not rejected.) — Sunan Abi Dawud & Tirmidhi</i>",
    "📚 <b>Hadith of the Day:</b>\nقال رسول الله ﷺ: «مَنْ قَرَأَ آيَةَ الْكُرْسِيِّ فِي دُبُرِ كُلِّ صَلَاةٍ مَكْتُوبَةٍ لَمْ يَمْنَعْهُ مِنْ دُخُولِ الْجَنَّةِ إِلَّا أَنْ يَمُوتَ»\n<i>(Whoever recites Ayat al-Kursi immediately after each prescribed prayer, there will be nothing standing between him and his entering Paradise except death.) — An-Nasa'i</i>",
]


# =====================================================================
# 2. TELEGRAM & STATE HELPER FUNCTIONS
# =====================================================================

def send_telegram_message(text: str, chat_id: str = CHAT_ID):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    res = requests.post(url, json=payload, timeout=15)
    if not res.ok:
        # Fallback to plain text if HTML entity parsing ever fails
        requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=15)


def send_telegram_audio(audio_url: str, caption: str, title: str, chat_id: str = CHAT_ID):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendAudio"
    payload = {
        "chat_id": chat_id,
        "audio": audio_url,
        "caption": caption,
        "title": title,
        "performer": "Mishary Rashid Alafasy",
        "parse_mode": "HTML",
    }
    requests.post(url, json=payload, timeout=20)


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_state(state: dict):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f)
    except Exception:
        pass


def should_trigger(event_key: str, target_dt: datetime.datetime, now_dt: datetime.datetime, state: dict, window_minutes: int = 15) -> bool:
    """Checks if target_dt is within the window AND hasn't been sent today."""
    today_str = now_dt.strftime("%Y-%m-%d")
    full_key = f"{today_str}:{event_key}"
    if state.get(full_key):
        return False
    diff_seconds = (now_dt - target_dt).total_seconds()
    if 0 <= diff_seconds < (window_minutes * 60):
        state[full_key] = True
        return True
    return False


def parse_time(raw_str: str, now_dt: datetime.datetime) -> datetime.datetime:
    clean_time = raw_str.split(" ")[0]
    hour, minute = map(int, clean_time.split(":"))
    return now_dt.replace(hour=hour, minute=minute, second=0, microsecond=0)


# =====================================================================
# 3. SPIRITUAL ENRICHMENT APIs (QURAN AYAH + AUDIO & 99 NAMES OF ALLAH)
# =====================================================================

def send_ayah_of_the_day(chat_id: str = CHAT_ID):
    """Fetches a Quranic verse with Arabic text, English meaning, and MP3 recitation."""
    ayah_num = random.randint(1, 6236)
    url = f"https://api.alquran.cloud/v1/ayah/{ayah_num}/editions/quran-uthmani,en.sahih,ar.alafasy"
    try:
        res = requests.get(url, timeout=12).json()
        if res.get("code") == 200:
            ar_data = res["data"][0]
            en_data = res["data"][1]
            audio_data = res["data"][2]

            surah_ar = ar_data["surah"]["name"]
            surah_en = ar_data["surah"]["englishName"]
            verse_num = ar_data["numberInSurah"]
            ar_text = ar_data["text"]
            en_text = en_data["text"]
            audio_url = audio_data.get("audio")

            caption = (
                f"📖 <b>Ayah of the Day — {surah_en} ({surah_ar}) [{verse_num}]</b>\n\n"
                f"﴿ {ar_text} ﴾\n\n"
                f"<i>\"{en_text}\"</i>"
            )
            if audio_url and len(caption) <= 1000:
                send_telegram_audio(audio_url, caption, f"{surah_en} - Ayah {verse_num}", chat_id)
            else:
                send_telegram_message(caption, chat_id)
                if audio_url:
                    send_telegram_audio(audio_url, f"🎧 {surah_en} ({verse_num})", f"{surah_en} {verse_num}", chat_id)
            return
    except Exception:
        pass
    send_telegram_message(random.choice(DAILY_DUAS), chat_id)


def get_asma_ul_husna(now_dt: datetime.datetime) -> str:
    """Fetches one of the 99 Names of Allah based on the day of the year."""
    day_of_year = now_dt.timetuple().tm_yday
    name_num = ((day_of_year - 1) % 99) + 1
    try:
        res = requests.get(f"https://api.aladhan.com/v1/asmaAlHusna/{name_num}", timeout=10).json()
        if res.get("code") == 200 and res.get("data"):
            item = res["data"][0]
            return (
                f"✨ <b>99 Names of Allah (#{item['number']}/99):</b>\n"
                f"<b>{item['name']}</b> ({item['transliteration']}) — <i>{item['en']['meaning']}</i>"
            )
    except Exception:
        pass
    return "✨ <b>Name of Allah:</b> اللَّهُ الرَّحْمَٰنُ الرَّحِيمُ (The Most Gracious, The Most Merciful)"


# =====================================================================
# 4. HIJRI CALENDAR & SPECIAL ISLAMIC EVENTS CHECKER
# =====================================================================

def get_hijri_events(hijri_day: int, hijri_month: int, is_evening: bool) -> list[str]:
    alerts = []
    # White Days (Al-Ayyam Al-Beed: 13, 14, 15 of every Hijri month)
    if is_evening and hijri_day in (12, 13, 14) and hijri_month != 9:
        alerts.append(
            f"🌕 <b>Sunnah Fasting Reminder (Al-Ayyam Al-Beed):</b>\n"
            f"Tomorrow is the <b>{hijri_day + 1}th</b> of the Hijri month (one of the Three White Days). "
            f"Make your intention tonight to fast tomorrow!"
        )
    elif not is_evening and hijri_day in (13, 14, 15) and hijri_month != 9:
        alerts.append(
            f"🌕 <b>White Day Today ({hijri_day}th Hijri):</b>\n"
            f"Today is one of the blessed White Days (الأيام البيض)."
        )

    # Muharram (Month 1): Tasu'a & Ashura (9th & 10th)
    if hijri_month == 1:
        if is_evening and hijri_day in (8, 9):
            alerts.append(
                "🌙 <b>Ashura Fasting Reminder:</b>\n"
                "Tomorrow is the 9th/10th of Muharram. Fasting the Day of Ashura expiates the sins of the previous year!"
            )

    # Ramadan (Month 9)
    if hijri_month == 9:
        if is_evening:
            alerts.append(
                "🌙 <b>Ramadan Iftar Dua:</b>\n"
                "«ذَهَبَ الظَّمَأُ وَابْتَلَّتِ الْعُرُوقُ، وَثَبَتَ الأَجْرُ إِنْ شَاءَ اللَّهُ»\n"
                "<i>(The thirst is gone, the veins are moistened, and the reward is confirmed, if Allah wills.)</i>"
            )
        else:
            alerts.append("🌙 <b>Ramadan Mubarak!</b> May Allah accept your fasting, prayers, and Qiyam today.")

    # Dhul-Hijjah (Month 12): First 10 Days & Day of Arafah
    if hijri_month == 12:
        if 1 <= hijri_day <= 9 and not is_evening:
            alerts.append(
                "🕋 <b>Blessed 10 Days of Dhul-Hijjah:</b>\n"
                "There are no days in which righteous deeds are more beloved to Allah than these ten days. "
                "Increase your Takbir, Tahmid, Tahlil, and Tasbih!"
            )
        if hijri_day == 8 and is_evening:
            alerts.append(
                "🕋 <b>Tomorrow is the Day of Arafah (9th Dhul-Hijjah)!</b>\n"
                "Make your intention tonight to fast tomorrow — fasting the Day of Arafah expiates the sins of the previous year and the coming year!"
            )
        if hijri_day == 9 and not is_evening:
            alerts.append(
                "🕋 <b>Today is the Day of Arafah!</b>\n"
                "The best Dua is the Dua on the Day of Arafah:\n"
                "«لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ، لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ»"
            )
    return alerts


# =====================================================================
# 5. INTERACTIVE CHAT COMMAND HANDLER (WORKS WITHOUT A 24/7 SERVER)
# =====================================================================

def process_pending_commands(timings: dict, hijri_str: str, now_dt: datetime.datetime):
    """Checks Telegram getUpdates queue and replies to any commands sent by the user."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    try:
        res = requests.get(url, params={"timeout": 2}, timeout=10).json()
        updates = res.get("result", [])
        if not updates:
            return

        last_update_id = updates[-1]["update_id"]
        # Acknowledge updates immediately so they are never processed twice
        requests.get(url, params={"offset": last_update_id + 1}, timeout=10)

        # Collect unique commands sent since the last check
        handled_commands = set()
        for upd in updates:
            msg = upd.get("message") or {}
            chat_id = str(msg.get("chat", {}).get("id", ""))
            text = (msg.get("text") or "").strip().lower()
            if not text or chat_id != str(CHAT_ID):
                continue

            cmd = text.split()[0].split("@")[0]
            if cmd in handled_commands:
                continue
            handled_commands.add(cmd)

            if cmd in ("/start", "/help", "hi", "hello", "salam"):
                send_telegram_message(
                    f"🌙 <b>Assalamu Alaikum! Muslim Remainder Bot ({CITY}, {COUNTRY})</b>\n"
                    f"📅 <b>Hijri Date:</b> {hijri_str}\n\n"
                    f"<b>Available Interactive Commands:</b>\n"
                    f"• /times — Today's full prayer & Sunnah schedule\n"
                    f"• /azkar — Complete Morning, Evening & Sleep Azkar\n"
                    f"• /dua — Instant authentic Dua\n"
                    f"• /ayah — Quran Ayah of the Day + Audio Recitation\n"
                    f"• /hadith — Authentic Hadith of the Day\n"
                    f"• /name — Today's Name of Allah (Asmaul Husna)\n"
                    f"• /tahajjud — Tonight's Tahajjud & Duha timings\n\n"
                    f"<i>(Note: Since this bot runs 100% free on GitHub Actions, command replies arrive on the next 15-minute cycle—or immediately if you click 'Run workflow'!)</i>"
                )
            elif cmd == "/times":
                schedule_lines = "\n".join([f"• <b>{p}:</b> {timings[p].split(' ')[0]}" for p in PRAYERS])
                send_telegram_message(
                    f"🕌 <b>Prayer Schedule — {CITY}, {COUNTRY}</b>\n"
                    f"📅 {hijri_str}\n\n"
                    f"{schedule_lines}\n\n"
                    f"🌅 <b>Sunrise:</b> {timings['Sunrise'].split(' ')[0]}\n"
                    f"🌌 <b>Last Third (Tahajjud):</b> {timings.get('Lastthird', '03:30').split(' ')[0]}"
                )
            elif cmd == "/azkar":
                send_telegram_message(MORNING_AZKAR)
                send_telegram_message(EVENING_AZKAR)
            elif cmd == "/dua":
                send_telegram_message(random.choice(DAILY_DUAS))
            elif cmd == "/hadith":
                send_telegram_message(random.choice(AUTHENTIC_HADITHS))
            elif cmd == "/ayah":
                send_ayah_of_the_day()
            elif cmd == "/name":
                send_telegram_message(get_asma_ul_husna(now_dt))
            elif cmd == "/tahajjud":
                sunrise_dt = parse_time(timings["Sunrise"], now_dt)
                duha_time = (sunrise_dt + datetime.timedelta(minutes=20)).strftime("%H:%M")
                last_third = timings.get("Lastthird", "03:30").split(" ")[0]
                send_telegram_message(
                    f"🌌 <b>Sunnah Prayer Timings ({CITY}):</b>\n\n"
                    f"• <b>Salatul Duha (Chourouk + 20m):</b> {duha_time}\n"
                    f"• <b>Tahajjud (Last Third of the Night):</b> Starts at {last_third} until Fajr ({timings['Fajr'].split(' ')[0]})"
                )
    except Exception as e:
        print(f"Command polling error: {e}")


# =====================================================================
# 6. MAIN SCHEDULER ENGINE
# =====================================================================

def main():
    url = "https://api.aladhan.com/v1/timingsByCity"
    params = {"city": CITY, "country": COUNTRY, "method": METHOD}
    res = requests.get(url, params=params, timeout=15).json()
    if res.get("code") != 200:
        print("Failed to fetch prayer times from AlAdhan API.")
        return

    data = res["data"]
    timings = data["timings"]
    tz = ZoneInfo(data["meta"]["timezone"])
    now = datetime.datetime.now(tz)

    hijri = data["date"]["hijri"]
    hijri_day = int(hijri["day"])
    hijri_month = int(hijri["month"]["number"])
    hijri_str = f"{hijri['day']} {hijri['month']['en']} ({hijri['month']['ar']}) {hijri['year']} AH"

    # 1. Process any interactive commands the user sent in Telegram
    process_pending_commands(timings, hijri_str, now)

    # 2. If triggered manually from GitHub Actions "Run workflow" button, send full dashboard test
    if os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch":
        sunrise_dt = parse_time(timings["Sunrise"], now)
        duha_str = (sunrise_dt + datetime.timedelta(minutes=20)).strftime("%H:%M")
        last_third_str = timings.get("Lastthird", "03:30").split(" ")[0]
        schedule_lines = "\n".join([f"• <b>{p}:</b> {timings[p].split(' ')[0]}" for p in PRAYERS])

        send_telegram_message(
            f"✅ <b>All-in-One Muslim Remainder Upgraded!</b>\n"
            f"📍 <b>Location:</b> {CITY}, {COUNTRY}\n"
            f"📅 <b>Hijri Date:</b> {hijri_str}\n\n"
            f"🕌 <b>Today's 5 Daily Prayers:</b>\n{schedule_lines}\n\n"
            f"☀️ <b>Salatul Duha:</b> {duha_str} <i>(20m after Sunrise)</i>\n"
            f"🌌 <b>Tahajjud (Last Third):</b> {last_third_str}\n\n"
            f"{get_asma_ul_husna(now)}\n\n"
            f"---\n{random.choice(DAILY_DUAS)}"
        )
        send_ayah_of_the_day()
        return

    state = load_state()

    # 3. Check 5 Daily Prayers + 15-Minute Pre-Prayer Wudu Alerts
    for prayer in PRAYERS:
        prayer_dt = parse_time(timings[prayer], now)
        raw_time = timings[prayer].split(" ")[0]

        # A) Pre-Prayer Wudu Alert (15 minutes before Adhan)
        wudu_dt = prayer_dt - datetime.timedelta(minutes=15)
        if should_trigger(f"pre_{prayer}", wudu_dt, now, state):
            extra = ""
            if hijri_month == 9 and prayer == "Fajr":
                extra = "\n🌙 <i>Suhoor / Imsak Warning: Fajr is in 15 minutes!</i>"
            send_telegram_message(
                f"💧 <b>15 Minutes Until {prayer} ({raw_time})</b>\n"
                f"Time to pause, renew your Wudu, and prepare for prayer.{extra}"
            )

        # B) Exact Adhan Alert + Post-Prayer Sunnah
        if should_trigger(f"adhan_{prayer}", prayer_dt, now, state):
            send_telegram_message(
                f"🕌 <b>It is time for {prayer} prayer ({raw_time}) in {CITY}.</b>\n\n"
                f"🤲 <b>Dua after Adhan:</b>\n"
                f"«اللَّهُمَّ رَبَّ هَذِهِ الدَّعْوَةِ التَّامَّةِ، وَالصَّلَاةِ الْقَائِمَةِ، آتِ مُحَمَّدًا الْوَسِيلَةَ وَالْفَضِيلَةَ...»\n\n"
                f"📿 <i>After-Prayer Sunnah:</i> Astaghfirullah (3x), Ayat al-Kursi, "
                f"SubhanAllah (33x), Alhamdulillah (33x), Allahu Akbar (34x)."
            )

            # At Fajr: Also send the Morning Timetable Card + Hijri Events + Asmaul Husna
            if prayer == "Fajr":
                sunrise_dt = parse_time(timings["Sunrise"], now)
                duha_str = (sunrise_dt + datetime.timedelta(minutes=20)).strftime("%H:%M")
                schedule_lines = "\n".join([f"• <b>{p}:</b> {timings[p].split(' ')[0]}" for p in PRAYERS])
                morning_events = "\n\n".join(get_hijri_events(hijri_day, hijri_month, is_evening=False))
                events_block = f"\n\n{morning_events}" if morning_events else ""

                send_telegram_message(
                    f"🗓️ <b>Daily Prayer Card — {hijri_str}</b>\n\n"
                    f"{schedule_lines}\n"
                    f"☀️ <b>Duha Prayer:</b> {duha_str}\n\n"
                    f"{get_asma_ul_husna(now)}{events_block}"
                )

    # 4. Morning Azkar (30 mins after Fajr) + Friday Surah Al-Kahf Package
    fajr_dt = parse_time(timings["Fajr"], now)
    if should_trigger("morning_azkar", fajr_dt + datetime.timedelta(minutes=30), now, state):
        send_telegram_message(f"{MORNING_AZKAR}\n\n---\n{random.choice(DAILY_DUAS)}")
        if now.weekday() == 4:  # Friday (0=Mon, 4=Fri)
            send_telegram_message(
                "🕌 <b>Jumu'ah Mubarak! (سنن يوم الجمعة)</b>\n\n"
                "1️⃣ <b>Recite Surah Al-Kahf:</b> It shines a light for you between this Friday and the next.\n"
                "2️⃣ <b>Abundant Salawat:</b> «اللَّهُمَّ صَلِّ وَسَلِّمْ عَلَى نَبِيِّنَا مُحَمَّدٍ»\n"
                "3️⃣ <b>Sunnah Acts:</b> Perform Ghusl, wear perfume, use Siwak, and head to the Masjid early."
            )

    # 5. Salatul Duha (Chourouk) Reminder (20 mins after Sunrise)
    sunrise_dt = parse_time(timings["Sunrise"], now)
    if should_trigger("duha_prayer", sunrise_dt + datetime.timedelta(minutes=20), now, state):
        send_telegram_message(
            "☀️ <b>Time for Salatul Duha (صلاة الضحى / الشروق)</b>\n"
            "Praying at least 2 Rak'ahs of Duha fulfills the charity due on every joint in your body (360 joints)."
        )

    # 6. Midday Enrichment: Quran Ayah (with Audio) + Authentic Hadith (15 mins after Dhuhr)
    dhuhr_dt = parse_time(timings["Dhuhr"], now)
    if should_trigger("dhuhr_knowledge", dhuhr_dt + datetime.timedelta(minutes=15), now, state):
        send_ayah_of_the_day()
        send_telegram_message(random.choice(AUTHENTIC_HADITHS))

    # 7. Evening Azkar (30 mins after Asr)
    asr_dt = parse_time(timings["Asr"], now)
    if should_trigger("evening_azkar", asr_dt + datetime.timedelta(minutes=30), now, state):
        send_telegram_message(f"{EVENING_AZKAR}\n\n---\n{random.choice(DAILY_DUAS)}")

    # 8. Friday "Golden Hour" Before Maghrib (Sa'at al-Istijabah — 45 mins before Maghrib)
    maghrib_dt = parse_time(timings["Maghrib"], now)
    if now.weekday() == 4 and should_trigger("friday_golden_hour", maghrib_dt - datetime.timedelta(minutes=45), now, state):
        send_telegram_message(
            "🤲 <b>Sa'at al-Istijabah (ساعة الاستجابة يوم الجمعة)</b>\n"
            "We are now in the final hour before Maghrib on Friday—a blessed time when no Muslim asks Allah for anything good except that He grants it. Devote these moments to sincere Dua!"
        )

    # 9. Evening Fasting & Hijri Reminders (15 mins after Maghrib)
    if should_trigger("maghrib_checks", maghrib_dt + datetime.timedelta(minutes=15), now, state):
        # Sunday (6) & Wednesday (2) evenings -> Remind for Monday/Thursday Sunnah Fast
        if now.weekday() in (6, 2) and hijri_month != 9:
            day_name = "Monday" if now.weekday() == 6 else "Thursday"
            send_telegram_message(
                f"🌙 <b>Sunnah Fasting Reminder ({day_name} Tomorrow):</b>\n"
                f"The Prophet ﷺ used to fast on Mondays and Thursdays because deeds are presented on those days. "
                f"Make your intention tonight if you wish to fast tomorrow!"
            )
        for alert_text in get_hijri_events(hijri_day, hijri_month, is_evening=True):
            send_telegram_message(alert_text)

    # 10. Sleep Azkar & Surah Al-Mulk Reminder (90 mins after Isha)
    isha_dt = parse_time(timings["Isha"], now)
    if should_trigger("sleep_azkar", isha_dt + datetime.timedelta(minutes=90), now, state):
        send_telegram_message(SLEEP_AZKAR)

    # 11. Tahajjud / Qiyam al-Layl (Start of the Last Third of the Night)
    if "Lastthird" in timings:
        tahajjud_dt = parse_time(timings["Lastthird"], now)
        if should_trigger("tahajjud", tahajjud_dt, now, state):
            send_telegram_message(
                "🌌 <b>The Last Third of the Night Has Begun (وقت التهجد والوتر)</b>\n"
                "Our Lord descends to the lowest heaven in the last third of every night, saying: "
                "<i>'Who is calling upon Me that I may answer him? Who is asking of Me that I may give him? Who is seeking My forgiveness that I may forgive him?'</i>"
            )

    save_state(state)


if __name__ == "__main__":
    main()
