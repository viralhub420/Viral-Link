import os
import random
import asyncio
import pytz
import threading
from datetime import datetime
from flask import Flask
from telegram import Bot
from telegram.constants import ParseMode

# CONFIGURATION
BOT_TOKEN = "8519388709:AAFegkbyQKYRUfUpRinjfAXjrUC8sfM9I7A" # এটি দ্রুত চেঞ্জ করে নিন
CHAT_IDS = ["@virallinkvideohub", "@viralmoviehubbd"]

links = [
    "https://otieu.com/4/10453524",
    "https://skbd355.42web.io",
    "https://earningguidebd01.blogspot.com"
]

posts = [
    {
        "title": "🔥 Viral Video Everyone Is Watching",
        "desc": "এই ভিডিওটা এখন সবাই দেখছে। শেষ পর্যন্ত দেখলে অবাক হবেন!",
        "img": "https://i.postimg.cc/26b5DjSh/1769324034004.jpg"
    },
    {
        "title": "🎬 Hot Movie Update Today",
        "desc": "আজকের সবচেয়ে আলোচিত মুভির আপডেট ও রিভিউ এখানে।",
        "img": "https://i.postimg.cc/6prRk0mt/FB-IMG-1769827515047.jpg"
    },
    {
        "title": "😱 Trending Content Going Viral",
        "desc": "এই কনটেন্টটা এখন ট্রেন্ডিং। আপনি মিস করবেন না!",
        "img": "https://i.postimg.cc/3Jpnw2c6/1769826704210.jpg"
    }
]

]

bot = Bot(token=BOT_TOKEN)
BD_TIME = pytz.timezone("Asia/Dhaka")

POST_TIMES = ["10:00", "15:10", "21:00"]
posted_today = set()

# ১. পোস্ট পাঠানোর ফাংশন (অ্যাসিঙ্ক)
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
        try:
            await bot.send_photo(
                chat_id=chat_id,
                photo=post["img"],
                caption=caption,
                parse_mode=ParseMode.HTML
            )
            print(f"✅ Sent to {chat_id}")
        except Exception as e:
            print(f"❌ Error sending to {chat_id}: {e}")

# ২. মেইন শিডিউলার লুপ (অ্যাসিঙ্ক)
async def scheduler_loop():
    print("🚀 Scheduler started...")
    while True:
        now = datetime.now(BD_TIME)
        current_time = now.strftime("%H:%M")
        today = now.strftime("%Y-%m-%d")

        for t in POST_TIMES:
            key = f"{today}_{t}"
            if current_time == t and key not in posted_today:
                await send_post()
                posted_today.add(key)
        
        # রাত ১২টায় লিস্ট রিসেট করা
        if current_time == "00:00":
            posted_today.clear()

        await asyncio.sleep(30) # ৩০ সেকেন্ড পরপর চেক করবে

# ৩. Flask (Keep-alive) Setup
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running successfully"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

# ৪. মেইন এন্ট্রি পয়েন্ট
if __name__ == "__main__":
    # Flask কে আলাদা থ্রেডে চালানো
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # বটের শিডিউলার লুপ শুরু করা
    try:
        asyncio.run(scheduler_loop())
    except KeyboardInterrupt:
        print("Bot stopped.")
