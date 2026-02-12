import os
import random
import asyncio
import pytz
import threading
import firebase_admin
from datetime import datetime
from flask import Flask
from firebase_admin import credentials, db
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# --- ১. আপনার কনফিগারেশন (আগের মতোই রাখা হয়েছে) ---
BOT_TOKEN = "8595737059:AAGS4FnyKqn99YFZB_7pNK0uB6K7GZYpx_8"
CHAT_IDS = ["@virallinkvideohub", "@viralmoviehubbd"]
MAIN_CHANNEL = "@viralmoviehubbd" # সাবস্ক্রাইব চেক করার চ্যানেল
MONETAG_LINK = "https://otieu.com/4/10453524"

# ফায়ারবেস কানেকশন
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://viralmoviehubbd-default-rtdb.firebaseio.com/'
    })
user_ref = db.reference('users')

# আপনার আগের লিঙ্কগুলো
links = [
    "https://otieu.com/4/10453524",
    "https://skbd355.42web.io",
    "https://earningguidebd01.blogspot.com"
]

# আপনার আগের পোস্টগুলো
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

BD_TIME = pytz.timezone("Asia/Dhaka")
POST_TIMES = ["07:00", "12:20", "21:00"]
posted_today = set()

# --- ২. অটো পোস্ট লজিক (আপনার আগের সিস্টেম) ---
async def scheduler_loop(bot_obj):
    while True:
        now = datetime.now(BD_TIME)
        current_time = now.strftime("%H:%M")
        today = now.strftime("%Y-%m-%d")
        
        for t in POST_TIMES:
            key = f"{today}_{t}"
            if current_time == t and key not in posted_today:
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
                        await bot_obj.send_photo(
                            chat_id=chat_id, 
                            photo=post["img"], 
                            caption=caption, 
                            parse_mode=ParseMode.HTML
                        )
                    except: pass
                posted_today.add(key)
        
        if current_time == "00:00":
            posted_today.clear()
        await asyncio.sleep(30)

# --- ৩. সাবস্ক্রিপশন ও রেফারেল লজিক ---
async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(MAIN_CHANNEL, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    ref_by = context.args[0] if context.args else None

    # ডাটাবেস সেভ
    u_data = user_ref.child(user_id).get()
    if not u_data:
        user_ref.child(user_id).set({'points': 0, 'ref_by': ref_by})
        if ref_by and ref_by != user_id:
            r_data = user_ref.child(ref_by).get()
            if r_data: user_ref.child(ref_by).update({'points': r_data.get('points', 0) + 1})

    if not await is_subscribed(context.bot, user_id):
        keyboard = [[InlineKeyboardButton("Join Channel 📢", url=f"https://t.me/{MAIN_CHANNEL[1:]}")],
                    [InlineKeyboardButton("Joined ✅", callback_data="check_join")]]
        await update.message.reply_text("❌ আগে চ্যানেলে জয়েন করুন!", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await show_menu(update)

async def show_menu(update):
    user_id = str(update.effective_user.id)
    u_info = user_ref.child(user_id).get()
    points = u_info.get('points', 0) if u_info else 0
    bot_info = await update.get_bot().get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    
    msg = f"🏆 আপনার রেফারেল পয়েন্ট: {points}\n🔗 ইনভাইট লিঙ্ক: {ref_link}"
    keyboard = [[InlineKeyboardButton("💰 টাকা ইনকাম (Ads)", url=MONETAG_LINK)]]
    
    target = update.message if update.message else update.callback_query.message
    await target.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query.data == "check_join":
        if await is_subscribed(context.bot, update.effective_user.id):
            await update.callback_query.message.delete()
            await show_menu(update)
        else:
            await update.callback_query.answer("❌ জয়েন করেননি!", show_alert=True)

# --- ৪. ফ্লাস্ক ও মেইন এন্ট্রি ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is Alive"

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=10000), daemon=True).start()
    
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    async def main():
        async with application:
            await application.initialize()
            await application.start()
            asyncio.create_task(scheduler_loop(application.bot))
            await application.updater.start_polling()
            while True: await asyncio.sleep(1)

    asyncio.run(main())
                             
