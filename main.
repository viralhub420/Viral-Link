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

if not firebase_admin._apps:
    try:
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred, {'databaseURL': 'https://viralmoviehubbd-default-rtdb.firebaseio.com/'})
    except: pass

user_ref = db.reference('users')
links = ["https://otieu.com/4/10453524", "https://t.me/Tetris1earnbot", "https://t.me/skbd355_bot"]
BD_TIME = pytz.timezone("Asia/Dhaka")

# --- ২. মেইন ফাংশনস ---

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
    
    msg = (
        f"🎬 Welcome to Viral Movie Hub\n\n"
        f"🏆 আপনার পয়েন্ট: {points}\n"
        f"🔗 ইনভাইট লিঙ্ক: https://t.me/{bot_info.username}?start={user_id}"
    )
    kb = [
        [InlineKeyboardButton("📺 Watch Movie (Unlock)", callback_data="step1_unlock")],
        [InlineKeyboardButton("🎁 Daily Bonus", url=MONETAG_LINK)],
        [InlineKeyboardButton("💳 Withdraw", callback_data="withdraw")]
    ]
    if update.callback_query:
        await update.callback_query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not user_ref.child(user_id).get():
        user_ref.child(user_id).set({'points': 0})
    
    if not await is_subscribed(context.bot, user_id):
        kb = [[InlineKeyboardButton("Join Channel 📢", url=f"https://t.me/{MAIN_CHANNEL[1:]}")],
              [InlineKeyboardButton("Joined ✅", callback_data="check_join")]]
        await update.message.reply_text("❌ আগে চ্যানেলে জয়েন করুন!", reply_markup=InlineKeyboardMarkup(kb))
    else:
        await show_main_menu(update, context)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "check_join":
        if await is_subscribed(context.bot, query.from_user.id):
            await query.message.delete()
            await show_main_menu(update, context)
        else:
            await query.answer("❌ আগে জয়েন করুন!", show_alert=True)

    elif query.data == "step1_unlock":
        # এখানে শুধু 'Unlock' বাটন আসবে, 'Done' বাটন নেই
        text = "⚠️ মুভি লিঙ্কটি পেতে প্রথমে নিচের বাটনে ক্লিক করে অ্যাড দেখুন।"
        kb = [
            [InlineKeyboardButton("🔗 1. Click to Unlock (Ad)", url=MONETAG_LINK)],
            [InlineKeyboardButton("📩 2. I have watched the Ad", callback_data="step2_done")]
        ]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb))

    elif query.data == "step2_done":
        # ইউজার ২য় বাটনে ক্লিক করার পর এখন 'Done' বাটন আসবে
        text = "✅ ধন্যবাদ! এখন নিচের বাটনে ক্লিক করে লিঙ্কটি নিন।"
        kb = [[InlineKeyboardButton("✅ Done / Get Link", callback_data="final_link")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb))

    elif query.data == "final_link":
        await query.message.edit_text(f"🚀 আপনার লিঙ্ক আনলক হয়েছে:\n👉 {random.choice(links)}")

    elif query.data == "withdraw":
        await query.answer("💳 টাকা তুলতে ৫০০ পয়েন্ট লাগবে।", show_alert=True)

# --- ৩. সার্ভার ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot Online"

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=10000), daemon=True).start()
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.run_polling()
