import os
import random
import asyncio
import pytz
import threading
import firebase_admin
from datetime import datetime
from flask import Flask
from firebase_admin import credentials, db
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# --- ১. কনফিগারেশন ---
BOT_TOKEN = "8595737059:AAGS4FnyKqn99YFZB_7pNK0uB6K7GZYpx_8" 
ADMIN_ID = 6311806060 
CHAT_IDS = ["@virallinkvideohub", "@viralmoviehubbd"] 
MAIN_CHANNEL = "@viralmoviehubbd" 
MONETAG_LINK = "https://otieu.com/4/10453524" 

# ফায়ারবেস কানেকশন
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://viralmoviehubbd-default-rtdb.firebaseio.com/'
        })
    except:
        print("Firebase setup error! Check your serviceAccountKey.json")

user_ref = db.reference('users')

links = [
    "https://otieu.com/4/10453524",
    "https://t.me/Tetris1earnbot",
    "https://t.me/skbd355_bot"
]

posts = [
    {"title": "Viral Video Update", "desc": "এই ভিডিওটা এখন ট্রেন্ডিং।", "img": "https://i.postimg.cc/26b5DjSh/1769324034004.jpg"},
    {"title": "Hot Movie Today", "desc": "সবচেয়ে আলোচিত মুভির আপডেট।", "img": "https://i.postimg.cc/6prRk0mt/FB-IMG-1769827515047.jpg"}
]

BD_TIME = pytz.timezone("Asia/Dhaka")
POST_TIMES = ["07:00", "12:20", "21:00"]
posted_today = set()

# --- ২. ব্যাকগ্রাউন্ড শিডিউলার ---

async def scheduler_loop(bot_obj):
    while True:
        try:
            now = datetime.now(BD_TIME)
            current_time = now.strftime("%H:%M")
            today = now.strftime("%Y-%m-%d")
            
            for t in POST_TIMES:
                key = f"{today}_{t}"
                if current_time == t and key not in posted_today:
                    post = random.choice(posts)
                    caption = f"<b>{post['title']}</b>\n\n{post['desc']}\n\n👉 <a href='{MONETAG_LINK}'>Watch Full Video</a>"
                    for chat_id in CHAT_IDS:
                        try:
                            await bot_obj.send_photo(chat_id=chat_id, photo=post["img"], caption=caption, parse_mode=ParseMode.HTML)
                        except: pass
                    posted_today.add(key)
            if current_time == "00:00": posted_today.clear()
        except: pass
        await asyncio.sleep(30)

# --- ৩. মেইন লজিক (সংশোধিত) ---

async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(MAIN_CHANNEL, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    u_info = user_ref.child(user_id).get()
    points = u_info.get('points', 0) if u_info else 0
    bot_info = await context.bot.get_me()
    
    # এরর এড়াতে লিঙ্কে HTML ট্যাগ ব্যবহার করা হয়নি
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    
    msg = (
        f"🎬 Welcome to Viral Movie Hub\n\n"
        f"🏆 আপনার পয়েন্ট: {points}\n"
        f"🔗 ইনভাইট লিঙ্ক: {ref_link}\n\n"
        f"মুভি দেখতে বা পয়েন্ট আয় করতে নিচের বাটনগুলো ব্যবহার করুন।"
    )
    
    keyboard = [
        [InlineKeyboardButton("📺 Watch Viral Video (Unlock Ad)", callback_data="unlock_flow")],
        [InlineKeyboardButton("🎁 Daily Bonus (Watch Ad)", url=MONETAG_LINK)],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")],
        [InlineKeyboardButton("💳 Withdraw Money", callback_data="withdraw")],
        [InlineKeyboardButton("💰 Extra Income", url=MONETAG_LINK)]
    ]
    
    if update.callback_query:
        await update.callback_query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    ref_by = context.args[0] if context.args else None

    if not user_ref.child(user_id).get():
        user_ref.child(user_id).set({'points': 0, 'ref_by': ref_by})
        if ref_by and ref_by != user_id:
            r_data = user_ref.child(ref_by).get()
            if r_data:
                user_ref.child(ref_by).update({'points': r_data.get('points', 0) + 1})

    if not await is_subscribed(context.bot, user_id):
        kb = [[InlineKeyboardButton("Join Channel 📢", url=f"https://t.me/{MAIN_CHANNEL[1:]}")],
              [InlineKeyboardButton("Joined ✅", callback_data="check_join")]]
        await update.message.reply_text("❌ আগে চ্যানেলে জয়েন করুন!", reply_markup=InlineKeyboardMarkup(kb))
    else:
        await show_main_menu(update, context)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)

    if query.data == "check_join":
        if await is_subscribed(context.bot, user_id):
            await query.message.delete()
            await show_main_menu(update, context)
        else:
            await query.answer("❌ আপনি এখনো জয়েন করেননি!", show_alert=True)

    elif query.data == "unlock_flow":
        text = "⚠️ মুভি লিঙ্কটি পেতে নিচের বাটনে ক্লিক করে অ্যাড দেখুন, তারপর ফিরে এসে Done এ ক্লিক করুন।"
        kb = [
            [InlineKeyboardButton("🔗 Click to Unlock", url=MONETAG_LINK)],
            [InlineKeyboardButton("✅ Done / View Link", callback_data="show_final_link")]
        ]
        await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

    elif query.data == "show_final_link":
        final_link = random.choice(links)
        await query.message.reply_text(f"✅ লিঙ্ক আনলক হয়েছে:\n👉 {final_link}")

# --- ৪. রানার ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot Online"

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=10000), daemon=True).start()
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    async def main_bot():
        async with application:
            await application.initialize()
            await application.start()
            asyncio.create_task(scheduler_loop(application.bot))
            await application.updater.start_polling()
            while True: await asyncio.sleep(1)

    asyncio.run(main_bot())
        
