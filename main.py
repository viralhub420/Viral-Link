import asyncio
import random
import time
from datetime import datetime
import pytz
from telegram import Bot
from telegram.constants import ParseMode
from flask import Flask
from threading import Thread

# ==============================
# CONFIG
# ==============================
BOT_TOKEN = "8595737059:AAGrKddWUKBqDulX1MfMAutMVtiETstoMXI"

CHAT_IDS = [
    "@virallinkvideohub",
    "@viralmoviehubbd"
]

links = [
    "https://otieu.com/4/10453524",
    "https://skbd355.42web.io",
    "https://earningguidebd01.blogspot.com"
]

posts = [
    {
        "title": "🔥 Viral Video Everyone Is Watching",
        "desc": "এই ভিডিওটা এখন সবাই দেখছে। শেষ পর্যন্ত দেখলে অবাক হবেন!",
        "img": "https://i.imgur.com/dZI0I9G.jpeg"
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

bot = Bot(token=BOT_TOKEN)
BD_TIME = pytz.timezone("Asia/Dhaka")

POST_TIMES = ["12:00", "15:00", "21:00"]  # বাংলাদেশ সময়
posted_today = set()

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

    print("✅ Post sent")

def scheduler_loop():
    while True:
        now = datetime.now(BD_TIME)
        current_time = now.strftime("%H:%M")
        today = now.strftime("%Y-%m-%d")

        for t in POST_TIMES:
            key = f"{today}_{t}"
            if current_time == t and key not in posted_today:
                asyncio.run(send_post())
                posted_today.add(key)

        time.sleep(30)

# ==============================
# Flask (keep alive)
# ==============================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running successfully"

Thread(target=scheduler_loop).start()
app.run(host="0.0.0.0", port=10000)
