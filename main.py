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

# --- ১. কনফিগারেশন ---
BOT_TOKEN = "8595737059:AAGS4FnyKqn99YFZB_7pNK0uB6K7GZYpx_8"
CHAT_IDS = ["@virallinkvideohub", "@viralmoviehubbd"] # অটো পোস্টের জন্য
MAIN_CHANNEL = "@viralmoviehubbd" # ফোর্স সাবস্ক্রাইব চেক করার জন্য
MONETAG_LINK = "https://otieu.com/4/10453524" # আপনার আর্নিং লিঙ্ক

# ফায়ারবেস সেটআপ
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://viralmoviehubbd-default-rtdb.firebaseio.com/'
    })
user_ref = db.reference('users')

# আগের ডাটা (লিঙ্ক ও পোস্ট)
links = [
    "https://otieu.com/4/10453524",
    "https://skbd355.42web.io",
    "https://earningguidebd01.blogspot.com"
]

posts = [
    {"title": "🔥 Viral Video", "desc": "এই ভিডিওটা এখন সবাই দেখছে।", "img": "https://i.postimg.cc/26b5DjSh/1769324034004.jpg"},
    {"title": "🎬 Movie Update", "desc": "আজকের আলোচিত মুভির আপডেট।", "img": "https://i.postimg.cc/6prRk0mt/FB-IMG-1769827515047.jpg"}
]

BD_TIME = pytz.timezone("Asia/Dhaka")
POST_TIMES = ["07:00", "12:20", "21:00"]
posted_today = set()

# --- ২. অটো পোস্ট ফাংশন ---
async def send_post(context: ContextTypes.DEFAULT_TYPE):
    post = random.choice(posts)
    link = random.choice(links)
    caption = f"<b>{post['title']}</b>\n\n<i>{post['desc']}</i>\n\n👉 <a href='{link}'>Click Here To Watch ▶️</a>"
    
    for chat_id in CHAT_IDS:
        try:
            await context.bot.send_photo(chat_id=chat_id, photo=post["img"], caption=caption, parse_mode=ParseMode.HTML)
        except Exception as e: print(f"Error: {e}")

async def scheduler_loop(app_bot):
    while True:
        now = datetime.now(BD_TIME)
        current_time = now.strftime("%H:%M")
        today = now.strftime("%Y-%m-%d")
        
        for t in POST_TIMES:
            key = f"{today}_{t}"
            if current_time == t and key not in posted_today:
                # ম্যানুয়ালি পোস্ট পাঠানোর জন্য টাস্ক ক্রিয়েট
                await send_post_manual(app_bot)
                posted_today.add(key)
        if current_time == "00:00": posted_today.clear()
        await asyncio.sleep(30)

async def send_post_manual(bot_obj):
    post = random.choice(posts)
    link = random.choice(links)
    caption = f"<b>{post['title']}</b>\n\n<i>{post['desc']}</i>\n\n👉 <a href='{link}'>Click Here To Watch ▶️</a>"
    for chat_id in CHAT_IDS:
        try: await bot_obj.send_photo(chat_id=chat_id, photo=post["img"], caption=caption, parse_mode=ParseMode.HTML)
        except: pass

# --- ৩. রেফারেল ও বট লজিক ---
async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(MAIN_CHANNEL, user_id)
        return member.status != 'left'
    except: return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    args = context.args
    ref_by = args[0] if args else None

    # ফায়ারবেস ডাটা হ্যান্ডলিং
    u_data = user_ref.child(user_id).get()
    if not u_data:
        user_ref.child(user_id).set({'points': 0, 'ref_by': ref_by})
        if ref_by and ref_by != user_id:
            r_data = user_ref.child(ref_by).get()
            if r_data:
                new_points = r_data.get('points', 0) + 1
                user_ref.child(ref_by).update({'points': new_points})

    if not await is_subscribed(context.bot, user_id):
        keyboard = [[InlineKeyboardButton("Join Channel 📢", url=f"https://t.me/{MAIN_CHANNEL[1:]}")],
                    [InlineKeyboardButton("Joined ✅", callback_data="check")]]
        await update.message.reply_text("❌ আগে চ্যানেলে জয়েন করুন!", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await show_menu(update)

async def show_menu(update):
    user_id = str(update.effective_user.id)
    u_info = user_ref.child(user_id).get()
    points = u_info.get('points', 0)
    bot_user = (await update.get_bot().get_me()).username
    ref_link = f"https://t.me/{bot_user}?start={user_id}"
    
    msg = f"🏆 আপনার রেফারেল পয়েন্ট: {points}\n🔗 আপনার লিঙ্ক: {ref_link}"
    keyboard = [[InlineKeyboardButton("💰 টাকা ইনকাম (Ads)", url=MONETAG_LINK)]]
    
    if update.message: await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
    else: await update.callback_query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "check":
        if await is_subscribed(context.bot, query.from_user.id):
            await query.message.delete()
            await show_menu(update)
        else:
            await query.answer("❌ আপনি এখনো জয়েন করেননি!", show_alert=True)

# --- ৪. ফ্লাস্ক ও মেইন ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is Alive"

def run_flask(): app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))

    # শিডিউলার লুপকে আলাদা টাস্ক হিসেবে চালানো
    loop = asyncio.get_event_loop()
    loop.create_task(scheduler_loop(application.bot))
    
    application.run_polling()
