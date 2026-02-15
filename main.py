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

# --- কনফিগারেশন (আপনার তথ্য দিন) ---
BOT_TOKEN = "8595737059:AAE8yY_qdUskQg1rPXCBaUejQbX79pJTkuM" # এখানে আপনার বট টোকেন দিন
ADMIN_ID = 6311806060 
CHANNEL_USERNAME = "@viralmoviehubbd"
FIREBASE_DB_URL = "https://viralmoviehubbd-default-rtdb.firebaseio.com/"
GITHUB_PAGES_URL = "https://viralhub420.github.io/Viral-Link/"

# ফায়ারবেস সেটআপ
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_DB_URL})

user_ref = db.reference('users')
movie_ref = db.reference('movies')

# --- ফাংশন: সাবস্ক্রিপশন চেক ---
async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

# --- ফাংশন: প্রগ্রেস বার তৈরি ---
def get_progress_bar(count, total=5):
    filled = "█" * count
    empty = "░" * (total - count)
    percent = (count / total) * 100
    return f"[{filled}{empty}] {int(percent)}%"

# --- মেইন মেনু (ক্লিন লুক) ---
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    if not await is_subscribed(context.bot, user_id):
        kb = [[InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
              [InlineKeyboardButton("✅ Joined (Check)", callback_data="check_join")]]
        msg = "❌ <b>অ্যাক্সেস ডিনাইড!</b>\n\nমুভি দেখতে হলে প্রথমে আমাদের চ্যানেলে জয়েন করে নিচের বাটনে ক্লিক করুন।"
    else:
        # ইউজার শুধু এই ক্লিন বাটনটি দেখবে
        msg = "🎬 <b>Viral Movie Hub</b>\n\nআপনার পছন্দের মুভিগুলো দেখতে নিচের বাটনে ক্লিক করুন।"
        kb = [[InlineKeyboardButton("🚀 Open Movie App", callback_data="open_app")]]

    target = update.callback_query.message if update.callback_query else update.message
    await target.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

# --- বাটন হ্যান্ডলার (রেফারেল লজিক এখানে) ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = str(update.effective_user.id)
    u_info = user_ref.child(user_id).get() or {'referrals': 0}
    referrals = min(u_info.get('referrals', 0), 5) # সর্বোচ্চ ৫ পর্যন্ত দেখাবে
    
    if query.data == "open_app":
        if referrals < 5:
            # ৫ জন পূর্ণ না হলে রেফারেল লক মেসেজ
            bot_info = await context.bot.get_me()
            ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
            progress = get_progress_bar(referrals)
            
            msg = (
                f"🎬 <b>Viral Movie Hub - Premium Access</b>\n\n"
                f"🔒 <b>আপনার অ্যাকাউন্ট বর্তমানে লক করা!</b>\n"
                f"মুভি লাইব্রেরি আনলক করতে ৫ জন বন্ধুকে ইনভাইত করুন।\n\n"
                f"👤 <b>আপনার অগ্রগতি:</b> <code>{referrals}/5</code>\n"
                f"📊 <b>স্ট্যাটাস:</b> {progress}\n\n"
                f"🔗 <b>ইনভাইট লিঙ্ক:</b> <code>{ref_link}</code>"
            )
            kb = [[InlineKeyboardButton("🚀 Invite Friends", switch_inline_query=f"\nমুভি দেখতে জয়েন করো!\n{ref_link}")],
                  [InlineKeyboardButton("🔙 Back", callback_data="back_main")]]
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
        else:
            # ৫ জন পূর্ণ থাকলে সরাসরি মিনি অ্যাপ বাটন
            msg = "✅ <b>অভিনন্দন!</b> মুভি লাইব্রেরি আনলক হয়েছে।"
            kb = [[InlineKeyboardButton("🎬 Watch Now", web_app={"url": GITHUB_PAGES_URL})]]
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
            
    elif query.data == "check_join" or query.data == "back_main":
        await show_main_menu(update, context)

# --- স্টার্ট কমান্ড ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id, args = str(update.effective_user.id), context.args
    is_new = not user_ref.child(user_id).get()
    
    if is_new:
        ref_by = args[0] if args else None
        user_ref.child(user_id).set({'referrals': 0, 'ref_by': ref_by})
        if ref_by and ref_by != user_id:
            r_data = user_ref.child(ref_by).get() or {'referrals': 0}
            new_count = r_data.get('referrals', 0) + 1
            user_ref.child(ref_by).update({'referrals': new_count})
            try:
                await context.bot.send_message(chat_id=ref_by, text=f"🎉 <b>নতুন রেফারেল!</b>\nঅগ্রগতি: {min(new_count, 5)}/5", parse_mode=ParseMode.HTML)
            except: pass
            
    await show_main_menu(update, context)

# --- মুভি পোস্ট (অ্যাডমিন) ---
async def post_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        data = " ".join(context.args).split("|")
        movie_ref.push({'name': data[0].strip(), 'url': data[1].strip(), 'img': data[2].strip()})
        await update.message.reply_text("✅ মুভি সফলভাবে অ্যাপে পোস্ট হয়েছে!")
    except:
        await update.message.reply_text("❌ লিখুন: /post নাম | ভিডিও লিঙ্ক | ছবির লিঙ্ক")

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("post", post_movie))
    app_bot.add_handler(CallbackQueryHandler(button_handler))
    print("Bot is running...")
    app_bot.run_polling()
    
