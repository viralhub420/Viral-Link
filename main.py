import os
import asyncio
import threading
from flask import Flask
import firebase_admin
from firebase_admin import credentials, db
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# --- ১. Render এর জন্য Web Port সেটআপ (Keep Alive) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is live and running!"

def run_flask():
    # Render অটোমেটিক পোর্ট নম্বর দেয়, তাই os.environ.get ব্যবহার করা হয়েছে
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# --- ২. কনফিগারেশন ---
# আপনার তথ্যগুলো এখানে সঠিকভাবে বসান
BOT_TOKEN = "আপনার_বট_টোকেন" 
CHANNEL_USERNAME = "@viralmoviehubbd" 
FIREBASE_DB_URL = "https://আপনার-প্রোজেক্ট-নাম.firebaseio.com/"

# ফায়ারবেস কানেকশন সেটআপ
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_DB_URL})
    except Exception as e:
        print(f"Firebase Error: {e}")

user_ref = db.reference('users')

# সাবস্ক্রিপশন চেক
async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# মেইন মেনু লজিক
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    u_info = user_ref.child(user_id).get()
    
    if not u_info:
        user_ref.child(user_id).set({'points': 0, 'referrals': 0})
        u_info = {'points': 0, 'referrals': 0}

    referrals = u_info.get('referrals', 0)
    bot_info = await context.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"

    # ১. ফোর্স জয়েন চেক
    if not await is_subscribed(context.bot, user_id):
        msg = "❌ <b>অ্যাক্সেস ডিনাইড!</b>\n\nবটটি ব্যবহার করতে আমাদের চ্যানেলে জয়েন করুন।"
        kb = [
            [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton("✅ Joined (Check)", callback_data="check_join")]
        ]
        target = update.callback_query.message if update.callback_query else update.message
        await target.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
        return

    # ২. ৫ রেফারেল চেক
    if referrals < 5:
        msg = (
            f"🎬 <b>Viral Movie Hub</b>\n\n"
            f"⚠️ আপনার অ্যাকাউন্ট লক করা!\n"
            f"মুভি আনলক করতে অন্তত ৫ জন বন্ধুকে ইনভাইট করতে হবে।\n\n"
            f"👥 রেফারেল: {referrals}/5\n"
            f"🔗 লিঙ্ক: <code>{ref_link}</code>"
        )
        kb = [[InlineKeyboardButton("🔗 Invite Friends", switch_inline_query=f"\nমুভি দেখতে এই বটে জয়েন করো!\n{ref_link}")]]
    else:
        msg = "✅ <b>অভিনন্দন!</b> আপনার অ্যাকাউন্ট এখন আনলক।\nপরবর্তী ধাপে আমরা এখানে মিনি অ্যাপ যুক্ত করব।"
        kb = [[InlineKeyboardButton("🚀 Open App (Coming Soon)", callback_data="coming_soon")]]

    if update.callback_query:
        await update.callback_query.message.edit_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

# স্টার্ট কমান্ড
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    args = context.args
    
    if not user_ref.child(user_id).get():
        ref_by = args[0] if args else None
        user_ref.child(user_id).set({'points': 0, 'referrals': 0, 'ref_by': ref_by})
        
        if ref_by and ref_by != user_id:
            r_data = user_ref.child(ref_by).get()
            if r_data:
                user_ref.child(ref_by).update({
                    'referrals': r_data.get('referrals', 0) + 1,
                    'points': r_data.get('points', 0) + 100
                })

    await show_main_menu(update, context)

# বাটন হ্যান্ডলার
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "check_join":
        if await is_subscribed(context.bot, query.from_user.id):
            try: await query.message.delete()
            except: pass
            await show_main_menu(update, context)
        else:
            await query.answer("⚠️ আপনি এখনো জয়েন করেননি!", show_alert=True)
    elif query.data == "coming_soon":
        await query.answer("🚀 ভাগ ১ শেষ হলে আমরা এখানে অ্যাপ যুক্ত করব।", show_alert=True)

# --- ৩. মেইন এক্সিকিউশন ---
if __name__ == "__main__":
    # Flask কে আলাদা থ্রেডে চালানো যাতে বটের কাজে বাধা না দেয়
    threading.Thread(target=run_flask, daemon=True).start()
    
    # টেলিগ্রাম বট শুরু
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    print("Bot is starting...")
    application.run_polling()
    
