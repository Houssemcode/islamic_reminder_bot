import datetime
import random
from zoneinfo import ZoneInfo
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = "8922959796:AAEkWBWA7m9NZidp4DE65vQ_UduXAdMHLC8"
PRAYERS = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]

MORNING_AZKAR = (
    "🌅 **Morning Azkar (أذكار الصباح)**\n\n"
    "1️⃣ **Ayat al-Kursi** (Recite once)\n"
    "_Allah! There is no deity except Him, the Ever-Living, the Sustainer of all existence..._\n\n"
    "2️⃣ **Sayyidul Istighfar:**\n"
    "اللَّهُمَّ أَنْتَ رَبِّي لَا إِلَهَ إِلَّا أَنْتَ، خَلَقْتَنِي وَأَنَا عَبْدُكَ...\n\n"
    "3️⃣ **Tasbih (3 times):**\n"
    "سُبْحَانَ اللَّهِ وَبِحَمْدِهِ: عَدَدَ خَلْقِهِ، وَرِضَا نَفْسِهِ، وَزِنَةَ عَرْشِهِ، وَمِدَادَ كَلِمَاتِهِ"
)

EVENING_AZKAR = (
    "🌇 **Evening Azkar (أذكار المساء)**\n\n"
    "1️⃣ **Ayat al-Kursi & Last 2 Verses of Surah Al-Baqarah**\n\n"
    "2️⃣ **Evening Remembrance:**\n"
    "أَمْسَيْنَا وَأَمْسَى الْمُلْكُ لِلَّهِ، وَالْحَمْدُ لِلَّهِ لَا إِلَهَ إِلَّا اللهُ وَحْدَهُ لَا شَرِيكَ لَهُ\n\n"
    "3️⃣ **Protection Dua (3 times):**\n"
    "بِسْمِ اللهِ الَّذِي لَا يَضُرُّ مَعَ اسْمِهِ شَيْءٌ فِي الْأَرْضِ وَلَا فِي السَّمَاءِ وَهُوَ السَّمِيعُ الْعَلِيمُ"
)

DAILY_DUAS = [
    "🤲 **Dua for Good in Both Worlds:**\nرَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ\n_(Our Lord, give us in this world that which is good and in the Hereafter that which is good, and protect us from the punishment of the Fire.)_",
    "🤲 **Dua for Steadfastness:**\nيَا مُقَلِّبَ الْقُلُوبِ ثَبِّتْ قَلْبِي عَلَى دِينِكَ\n_(O Turner of the hearts, make my heart firm upon Your religion.)_",
    "🤲 **Dua for Forgiveness & Relief:**\nلَا إِلَهَ إِلَّا أَنْتَ سُبْحَانَكَ إِنِّي كُنْتُ مِنَ الظَّالِمِينَ\n_(There is no deity except You; exalted are You. Indeed, I have been of the wrongdoers.)_",
    "🤲 **Dua for Beneficial Knowledge:**\nاللَّهُمَّ إِنِّي أَسْأَلُكَ عِلْمًا نَافِعًا، وَرِزْقًا طَيِّبًا، وَعَمَلًا مُتَقَبَّلًا\n_(O Allah, I ask You for beneficial knowledge, goodly provision, and acceptable deeds.)_",
]


def fetch_prayer_data(city: str, country: str):
    """Fetches prayer timings from the free AlAdhan API."""
    url = "https://api.aladhan.com/v1/timingsByCity"
    params = {"city": city, "country": country}
    response = requests.get(url, params=params, timeout=10)
    data = response.json()
    return data["data"] if data.get("code") == 200 else None


async def send_prayer_alert(context: ContextTypes.DEFAULT_TYPE):
    """Sends the Salah reminder along with post-prayer Dhikr."""
    job = context.job
    prayer_name = job.data
    text = (
        f"🕌 **It is time for {prayer_name} prayer.**\n\n"
        f"📿 _After-Prayer Sunnah:_ Astaghfirullah (3x), Ayat al-Kursi, "
        f"SubhanAllah (33x), Alhamdulillah (33x), Allahu Akbar (34x)."
    )
    await context.bot.send_message(chat_id=job.chat_id, text=text, parse_mode="Markdown")


async def send_azkar_alert(context: ContextTypes.DEFAULT_TYPE):
    """Sends scheduled Morning or Evening Azkar plus a random daily Dua."""
    job = context.job
    random_dua = random.choice(DAILY_DUAS)
    await context.bot.send_message(
        chat_id=job.chat_id,
        text=f"{job.data}\n\n---\n{random_dua}",
        parse_mode="Markdown",
    )


async def schedule_daily_jobs(context: ContextTypes.DEFAULT_TYPE):
    """Schedules today's 5 Salah alerts + Morning & Evening Azkar."""
    job_data = context.job.data
    chat_id = context.job.chat_id
    api_data = fetch_prayer_data(job_data["city"], job_data["country"])
    if not api_data:
        return

    timings = api_data["timings"]
    tz = ZoneInfo(api_data["meta"]["timezone"])
    now = datetime.datetime.now(tz)

    for old_job in context.job_queue.get_jobs_by_name(f"daily_items_{chat_id}"):
        old_job.schedule_removal()

    for prayer in PRAYERS:
        raw_time = timings[prayer].split(" ")[0]
        hour, minute = map(int, raw_time.split(":"))
        prayer_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        if prayer_dt > now:
            context.job_queue.run_once(
                send_prayer_alert,
                when=prayer_dt,
                chat_id=chat_id,
                name=f"daily_items_{chat_id}",
                data=prayer,
            )

        # Schedule Morning Azkar 25 minutes after Fajr
        if prayer == "Fajr":
            morning_dt = prayer_dt + datetime.timedelta(minutes=25)
            if morning_dt > now:
                context.job_queue.run_once(
                    send_azkar_alert,
                    when=morning_dt,
                    chat_id=chat_id,
                    name=f"daily_items_{chat_id}",
                    data=MORNING_AZKAR,
                )

        # Schedule Evening Azkar 25 minutes after Asr
        if prayer == "Asr":
            evening_dt = prayer_dt + datetime.timedelta(minutes=25)
            if evening_dt > now:
                context.job_queue.run_once(
                    send_azkar_alert,
                    when=evening_dt,
                    chat_id=chat_id,
                    name=f"daily_items_{chat_id}",
                    data=EVENING_AZKAR,
                )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌙 **Assalamu Alaikum! Welcome to your Free Salah & Azkar Bot.**\n\n"
        "**Commands:**\n"
        "• `/setcity City Country` — Enable automated Salah & Azkar alerts (e.g. `/setcity SoukAhras Algeria`)\n"
        "• `/times` — View today's prayer schedule\n"
        "• `/azkar` — Read Morning & Evening Azkar anytime\n"
        "• `/dua` — Receive an instant authentic Dua",
        parse_mode="Markdown",
    )


async def set_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: `/setcity City Country` (e.g., `/setcity Algiers Algeria`)", parse_mode="Markdown")
        return

    city = context.args[0]
    country = " ".join(context.args[1:])
    chat_id = update.effective_chat.id

    api_data = fetch_prayer_data(city, country)
    if not api_data:
        await update.message.reply_text("❌ Could not find that location. Please check your spelling.")
        return

    tz_name = api_data["meta"]["timezone"]
    tz = ZoneInfo(tz_name)

    for old_job in context.job_queue.get_jobs_by_name(f"refresh_{chat_id}"):
        old_job.schedule_removal()

    user_config = {"city": city, "country": country}
    context.chat_data["location"] = user_config

    context.job_queue.run_once(schedule_daily_jobs, when=1, chat_id=chat_id, data=user_config)
    context.job_queue.run_daily(
        schedule_daily_jobs,
        time=datetime.time(hour=0, minute=5, tzinfo=tz),
        chat_id=chat_id,
        name=f"refresh_{chat_id}",
        data=user_config,
    )

    timings = api_data["timings"]
    schedule_text = "\n".join([f"• **{p}:** {timings[p]}" for p in PRAYERS])
    await update.message.reply_text(
        f"✅ **Automated Salah & Azkar Alerts Enabled!**\n"
        f"📍 Location: **{city.title()}, {country.title()}** ({tz_name})\n\n"
        f"**Today's Salah Timings:**\n{schedule_text}\n\n"
        f"_Morning Azkar will be sent 25 mins after Fajr, and Evening Azkar 25 mins after Asr._",
        parse_mode="Markdown",
    )


async def show_times(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loc = context.chat_data.get("location")
    if not loc:
        await update.message.reply_text("Please set your city first using `/setcity City Country`.", parse_mode="Markdown")
        return
    api_data = fetch_prayer_data(loc["city"], loc["country"])
    timings = api_data["timings"]
    schedule_text = "\n".join([f"• **{p}:** {timings[p]}" for p in PRAYERS])
    await update.message.reply_text(f"🕌 **Today's Prayer Times:**\n{schedule_text}", parse_mode="Markdown")


async def send_dua(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(DAILY_DUAS), parse_mode="Markdown")


async def send_azkar_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"{MORNING_AZKAR}\n\n---\n\n{EVENING_AZKAR}", parse_mode="Markdown")


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setcity", set_city))
    app.add_handler(CommandHandler("times", show_times))
    app.add_handler(CommandHandler("dua", send_dua))
    app.add_handler(CommandHandler("azkar", send_azkar_menu))
    print("Salah & Azkar Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
