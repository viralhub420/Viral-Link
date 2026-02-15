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
ADMIN_ID = 6311806060 
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

# --- প্রগ্রেস বার তৈরির ফাংশন ---
def get_progress_bar(count, total=5):
    filled = "█" * count
    empty = "░" * (total - count)
    percent = (count / total) * 100
    return f"[{filled}{empty}] {int(percent)}%"

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    u_info = user_ref.child(user_id).get() or {'referrals': 0}
    referrals = u_info.get('referrals', 0)
    if referrals > 5: referrals = 5 # সর্বোচ্চ ৫ পর্যন্ত দেখাবে
    
    bot_info = await context.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    progress = get_progress_bar(referrals)

    if not await is_subscribed(context.bot, user_id):
        kb = [[InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
              [InlineKeyboardButton("✅ Joined (Check)", callback_data="check_join")]]
        msg = "❌ <b>অ্যাক্সেস ডিনাইড!</b>\n\nমুভি দেখতে হলে প্রথমে আমাদের চ্যানেলে জয়েন করে নিচের বাটনে ক্লিক করুন।"
    elif referrals < 5:
        # --- প্রফেশনাল রেফারেল মেসেজ ---
        msg = (
            f"🎬 <b>Viral Movie Hub - Premium Access</b>\n\n"
            f"🔒 <b>আপনার অ্যাকাউন্ট বর্তমানে লক করা!</b>\n"
            f"আমাদের মুভি লাইব্রেরি আনলক করতে ৫ জন বন্ধুকে ইনভাইট করুন।\n\n"
            f"👤 <b>আপনার অগ্রগতি:</b> <code>{referrals}/5</code>\n"
            f"📊 <b>স্ট্যাটাস:</b> {progress}\n\n"
            f"🔗 <b>আপনার ইনভাইট লিঙ্ক:</b>\n<code>{ref_link}</code>\n\n"
            f"🚀 <i>ইনভাইট পূর্ণ হলে 'Open Movie App' বাটনটি অটোমেটিক চলে আসবে।</i>"
        )
        kb = [[InlineKeyboardButton("🚀 Invite Friends", switch_inline_query=f"\nমুভি দেখতে জয়েন করো!\n{ref_link}")]]
    else:
        # --- আনলক হওয়ার পর মেসেজ ---
        msg = "✅ <b>অভিনন্দন!</b> আপনার অ্যাকাউন্ট এখন প্রিমিয়াম।\nনিচের বাটনে ক্লিক করে সব মুভি ফ্রিতে উপভোগ করুন।"
        kb = [[InlineKeyboardButton("🎬 Open Movie App", web_app={"url": GITHUB_PAGES_URL})]]

    target = update.callback_query.message if update.callback_query else update.message
    await target.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id, args = str(update.effective_user.id), context.args
    is_new_user = not user_ref.child(user_id).get()
    
    if is_new_user:
        ref_by = args[0] if args else None
        user_ref.child(user_id).set({'referrals': 0, 'ref_by': ref_by})
        # রেফারেল কাউন্ট বৃদ্ধি
        if ref_by and ref_by != user_id:
            r_data = user_ref.child(ref_by).get() or {'referrals': 0}
            new_count = r_data.get('referrals', 0) + 1
            user_ref.child(ref_by).update({'referrals': new_count})
            # রেফারারকে নোটিফিকেশন পাঠানো
            try:
                await context.bot.send_message(
                    chat_id=ref_by, 
                    text=f"🎉 <b>নতুন সফল রেফারেল!</b>\nআপনার বর্তমান অগ্রগতি: {new_count}/5",
                    parse_mode=ParseMode.HTML
                )
            except: pass
            
    await show_main_menu(update, context)

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
                                    
