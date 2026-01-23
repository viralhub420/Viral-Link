import asyncio
import random
import schedule
import time
import os
from telegram import Bot
from telegram.constants import ParseMode
from flask import Flask
from threading import Thread

# ==============================
# 🔐 CONFIG
# ==============================
BOT_TOKEN = os.environ.get("BOT_TOKEN") or "8595737059:AAGrKddWUKBqDulX1MfMAutMVtiETstoMXI"

CHAT_IDS = [
    "@virallinkvideohub",   # Group
    "@viralmoviehubbd"      # Channel
]

bot = Bot(token=BOT_TOKEN)

# ==============================
# 🔗 LINKS
# ==============================
links = [
    "https://otieu.com/4/10453524",
    "https://skbd355.42web.io",
    "https://earningguidebd01.blogspot.com"
]

# ==============================
# 🖼️ POST CONTENT
# ==============================
posts = [
    {
        "title": "🔥 Viral Video Everyone Is Watching",
        "desc": "এই ভিডিওটা এখন সবাই দেখছে। শেষ পর্যন্ত দেখলে অবাক হবেন!",
        "img": "https://i.imgur.com/9ZQZ4ZC.jpg"
    },
    {
        "title": "🎬 Hot Movie Update Today",
        "desc": "আজকের সবচেয়ে আলোচিত মুভির আপডেট ও রিভিউ এখানে।",
        "img": "https://i.imgur.com/4M7IWwP.jpg"
    },
    {
        "title": "😱 Trending Content Going Viral",
        "desc": "এই কনটেন্টটা এখন ট্রেন্ডিং। আপনি মিস করবেন না!",
        "img": "https://i.imgur.com/1o1n9Qf.jpg"
    }
]

# ==============================
# 🚀 SEND POST
# ==============================
async def send_post():
    post = random.choice(posts)
    link = random.choice(links)

    caption = (
        f"<b>{post['title']}</b>\n\n"
        f"<i>{post['desc']}</i>\n\n"
        f"👉 <a href='{link}'>Click Here To Watch ▶️</a>\n\n"
        f"<i>Powered by Viral Hub</i>"
    )

    for chat_id in CHAT_IDS:
        await bot.send_photo(
            chat_id=chat_id,
            photo=post["img"],
            caption=caption,
            parse_mode=ParseMode.HTML
        )

    print("✅ Post sent to group & channel")

def job():
    asyncio.run(send_post())

# ==============================
# ⏰ AUTO SCHEDULE
# ==============================
schedule.every().day.at("10:00").do(job)
schedule.every().day.at("15:00").do(job)
schedule.every().day.at("21:00").do(job)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(30)

# ==============================
# 🌐 FLASK (Render keep alive)
# ==============================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running successfully"

Thread(target=run_scheduler).start()

app.run(host="0.0.0.0", port=10000)
