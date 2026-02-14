import os
import asyncio
import threading
from flask import Flask
import firebase_admin
from firebase_admin import credentials, db
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

app = Flask(__name__)
@app.route('/')
def home(): return "Bot is live!"
def run_flask(): app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

# --- কনফিগারেশন ---
BOT_TOKEN = "8595737059:AAE8yY_qdUskQg1rPXCBaUejQbX79pJTkuM" # আপনার টোকেন দিন
ADMIN_ID = 6311806060 # আপনার টেলিগ্রাম আইডি
CHANNEL_USERNAME = "@viralmoviehubbd"
FIREBASE_DB_URL = "https://viralmoviehubbd-default-rtdb.firebaseio.com/"
GITHUB_PAGES_URL = "https://viralhub420.github.io/Viral-Link/"

if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_DB_URL})

user_ref = db.reference('users')
movie_ref = db.reference('movies')

async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    u_info = user_ref.child(user_id).get() or {'referrals': 0}
    referrals = u_info.get('referrals', 0)
    bot_info = await context.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"

    if not await is_subscribed(context.bot, user_id):
        kb = [[InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
              [InlineKeyboardButton("✅ Joined (Check)", callback_data="check_join")]]
        msg = "❌ <b>অ্যাক্সেস ডিনাইড!</b>\nচ্যানেলে জয়েন করে চেক বাটনে ক্লিক করুন।"
    elif referrals < 5:
        msg = f"🎬 <b>Viral Movie Hub</b>\n\n⚠️ অ্যাকাউন্ট লক! ৫ রেফারেল প্রয়োজন।\n👥 আপনার রেফারেল: {referrals}/5\n🔗 <code>{ref_link}</code>"
        kb = [[InlineKeyboardButton("🔗 Invite Friends", switch_inline_query=f"\nমুভি দেখতে জয়েন করো!\n{ref_link}")]]
    else:
        msg = "✅ <b>অভিনন্দন!</b> অ্যাকাউন্ট আনলক হয়েছে।"
        kb = [[InlineKeyboardButton("🚀 Open Movie App", web_app={"url": GITHUB_PAGES_URL})]]

    target = update.callback_query.message if update.callback_query else update.message
    await target.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id, args = str(update.effective_user.id), context.args
    if not user_ref.child(user_id).get():
        ref_by = args[0] if args else None
        user_ref.child(user_id).set({'referrals': 0, 'ref_by': ref_by})
        if ref_by and ref_by != user_id:
            r_data = user_ref.child(ref_by).get() or {'referrals': 0}
            user_ref.child(ref_by).update({'referrals': r_data.get('referrals', 0) + 1})
    await show_main_menu(update, context)

# --- নতুন মুভি পোস্ট কমান্ড (শুধুমাত্র অ্যাডমিন) ---
async def post_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        data = " ".join(context.args).split("|")
        movie_ref.push({'name': data[0].strip(), 'url': data[1].strip(), 'img': data[2].strip()})
        await update.message.reply_text("✅ মুভি সফলভাবে অ্যাপে পোস্ট হয়েছে!")
    except:
        await update.message.reply_text("❌ ভুল ফরমেট! লিখুন:\n/post নাম | ভিডিও লিঙ্ক | ছবির লিঙ্ক")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    if await is_subscribed(context.bot, update.effective_user.id):
        await show_main_menu(update, context)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("post", post_movie))
    app_bot.add_handler(CallbackQueryHandler(button_handler))
    print("Bot is running...")
    app_bot.run_polling()
        
