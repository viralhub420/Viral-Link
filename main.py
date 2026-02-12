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
BOT_TOKEN = "8595737059:AAGS4FnyKqn99YFZB_7pNK0uB6K7GZYpx_8" # এখানে আপনার টোকেন দিন
ADMIN_ID = 6311806060 
CHAT_IDS = ["@virallinkvideohub", "@viralmoviehubbd"] 
MAIN_CHANNEL = "@viralmoviehubbd" 
MONETAG_LINK = "https://otieu.com/4/10453524" 

# ফায়ারবেস কানেকশন
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://viralmoviehubbd-default-rtdb.firebaseio.com/'
    })
user_ref = db.reference('users')

links = [
    "https://otieu.com/4/10453524",
    "https://t.me/Tetris1earnbot",
    "https://t.me/skbd355_bot"
]

posts = [
    {"title": "🔥 Viral Video Everyone Is Watching", "desc": "এই ভিডিওটা এখন সবাই দেখছে। শেষ পর্যন্ত দেখলে অবাক হবেন!", "img": "https://i.postimg.cc/26b5DjSh/1769324034004.jpg"},
    {"title": "🎬 Hot Movie Update Today", "desc": "আজকের সবচেয়ে আলোচিত মুভির আপডেট ও রিভিউ এখানে।", "img": "https://i.postimg.cc/6prRk0mt/FB-IMG-1769827515047.jpg"},
    {"title": "😱 Trending Content Going Viral", "desc": "এই কনটেন্টটা এখন ট্রেন্ডিং। আপনি মিস করবেন না!", "img": "https://i.postimg.cc/3Jpnw2c6/1769826704210.jpg"}
]

BD_TIME = pytz.timezone("Asia/Dhaka")
POST_TIMES = ["07:00", "12:20", "21:00"]
posted_today = set()

# --- ২. ব্যাকগ্রাউন্ড লজিক ---

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
                    link = MONETAG_LINK
                    caption = f"<b>{post['title']}</b>\n\n<i>{post['desc']}</i>\n\n👉 <a href='{link}'>Click Here To Unlock & Watch ▶️</a>"
                    for chat_id in CHAT_IDS:
                        try:
                            await bot_obj.send_photo(chat_id=chat_id, photo=post["img"], caption=caption, parse_mode=ParseMode.HTML)
                        except: pass
                    posted_today.add(key)
            if current_time == "00:00": posted_today.clear()
        except: pass
        await asyncio.sleep(30)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ আপনি অ্যাডমিন নন!")
        return
    if not context.args:
        await update.message.reply_text("📖 ব্যবহার: /broadcast [মেসেজ]")
        return
    
    msg_text = " ".join(context.args)
    users = user_ref.get()
    if not users: return
    
    count = 0
    for u_id in users:
        try:
            await context.bot.send_message(chat_id=int(u_id), text=msg_text)
            count += 1
            await asyncio.sleep(0.05)
        except: pass
    await update.message.reply_text(f"✅ {count} জনকে পাঠানো হয়েছে।")

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
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    
    msg = (
        f"🎬 **Welcome to Viral Movie Hub**\n\n"
        f"🏆 পয়েন্ট: {points}\n"
        f"🔗 রেফারেল লিঙ্ক: {ref_link}\n\n"
        f"মুভি দেখতে নিচের বাটনগুলো ব্যবহার করুন।"
    )
    keyboard = [
        [InlineKeyboardButton("📺 Watch Viral Video (Unlock Ad)", callback_data="unlock_flow")],
        [InlineKeyboardButton("🎁 Daily Bonus (Watch Ad)", url=MONETAG_LINK)],
        [InlineKeyboardButton("🏆 Top Referrers", callback_data="leaderboard")],
        [InlineKeyboardButton("💳 Withdraw Money", callback_data="withdraw")],
        [InlineKeyboardButton("💰 Extra Income", url=MONETAG_LINK)]
    ]
    
    if update.callback_query:
        await update.callback_query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

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
        keyboard = [
            [InlineKeyboardButton("Join Channel 📢", url=f"https://t.me/{MAIN_CHANNEL[1:]}")],
            [InlineKeyboardButton("Joined ✅", callback_data="check_join")]
        ]
        await update.message.reply_text("❌ আগে চ্যানেলে জয়েন করুন!", reply_markup=InlineKeyboardMarkup(keyboard))
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
            await query.answer("❌ আপনি এখনো জয়েন করেননি!", show_alert=True)

    elif query.data == "unlock_flow":
        kb = [[InlineKeyboardButton("🔗 Click to Unlock", url=MONETAG_LINK)],
              [InlineKeyboardButton("✅ Done / View Link", callback_data="show_final_link")]]
        await query.message.reply_text("⚠️ লিঙ্কটি পেতে আগে ৫ সেকেন্ড অ্যাড দেখুন:", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data == "show_final_link":
        await query.message.reply_text(f"✅ লিঙ্ক আনলক হয়েছে:\n👉 {random.choice(links)}")

    elif query.data == "leaderboard":
        await query.answer("🏆 লিডারবোর্ড শীঘ্রই আসবে!", show_alert=True)

    elif query.data == "withdraw":
        await query.answer("💳 টাকা তুলতে ৫০০ পয়েন্ট লাগবে।", show_alert=True)

# --- ৪. রানার ---
app = Flask(__name__)
@app.route('/')
def home(): return "Online"

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=10000), daemon=True).start()
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CallbackQueryHandler(button_handler))

    async def main_loop():
        async with application:
            await application.initialize()
            await application.start()
            asyncio.create_task(scheduler_loop(application.bot))
            await application.updater.start_polling()
            while True: await asyncio.sleep(1)

    asyncio.run(main_loop())
