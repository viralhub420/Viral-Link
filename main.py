import os
import asyncio
import threading
from flask import Flask
import firebase_admin
from firebase_admin import credentials, db
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from datetime import datetime

app = Flask(__name__)
@app.route('/')
def home(): return "Bot is live!"
def run_flask(): app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

# --- কনফিগারেশন ---
BOT_TOKEN = "8595737059:AAE8yY_qdUskQg1rPXCBaUejQbX79pJTkuM" 
ADMIN_ID = 6311806060 
CHANNEL_USERNAME = "@viralmoviehubbd"
FIREBASE_DB_URL = "https://viralmoviehubbd-default-rtdb.firebaseio.com/"
GITHUB_PAGES_URL = "https://viralhub420.github.io/Viral-Link/"

# Monetag SDK & CPAGrip Links
MONETAG_SDK_LINK = "https://libtl.com/sdk.js?zone=10500197"
TASK_LINKS = {
    "task1": " ", # আপনার লিঙ্ক এখানে বসান
    "task2": "CPAGRIP_LINK_2",
    "task3": "CPAGRIP_LINK_3"
}

if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_DB_URL})

user_ref = db.reference('users')

# --- সাবস্ক্রিপশন চেক ---
async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

# --- প্রগ্রেস বার ---
def get_progress_bar(count, total=5):
    filled = "█" * count
    empty = "░" * (total - count)
    return f"[{filled}{empty}] {int((count/total)*100)}%"

# --- মেইন মেনু আপডেট ---
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not await is_subscribed(context.bot, user_id):
        kb = [[InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
              [InlineKeyboardButton("✅ Joined (Check)", callback_data="check_join")]]
        msg = "❌ <b>অ্যাক্সেস ডিনাইড!</b>\nচ্যানেলে জয়েন করে চেক বাটনে ক্লিক করুন।"
    else:
        msg = "🎬 <b>Viral Movie Hub</b>\n\nনিচের অপশনগুলো ব্যবহার করুন:"
        kb = [
            [InlineKeyboardButton("🚀 Open Movie App", callback_data="open_app")],
            [InlineKeyboardButton("🎁 My Offers (Earn)", callback_data="open_tasks")],
            [InlineKeyboardButton("📅 Daily Bonus", callback_data="claim_bonus")],
            [InlineKeyboardButton("💰 Wallet & Withdraw", callback_data="open_wallet")]
        ]
    target = update.callback_query.message if update.callback_query else update.message
    await target.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

# --- বাটন হ্যান্ডলার (সব লজিক এখানে) ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(update.effective_user.id)
    u_info = user_ref.child(user_id).get() or {'referrals': 0, 'coins': 0, 'completed_tasks': []}
    
    # ১. মুভি অ্যাপ আনলক (Invite + Monetag)
    if query.data == "open_app":
        referrals = min(u_info.get('referrals', 0), 5)
        if referrals < 5:
            bot_info = await context.bot.get_me()
            ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
            msg = f"🔒 <b>অ্যাকাউন্ট লক!</b>\n৫ জন বন্ধুকে ইনভাইট করুন।\n\n📊 {get_progress_bar(referrals)}\n🔗 <code>{ref_link}</code>"
            kb = [[InlineKeyboardButton("🚀 Invite Friends", switch_inline_query=f"\nমুভি দেখতে জয়েন করো!\n{ref_link}")],
                  [InlineKeyboardButton("🔙 Back", callback_data="back_main")]]
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
        else:
            msg = "✅ আপনার ইনভাইট পূর্ণ হয়েছে!\nমুভি আনলক করতে নিচের অ্যাডটি দেখুন।"
            kb = [[InlineKeyboardButton("📺 Ad to Unlock (Monetag)", url=MONETAG_SDK_LINK)],
                  [InlineKeyboardButton("🎬 Watch Now (Open App)", web_app={"url": GITHUB_PAGES_URL})]]
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

    # ২. My Offers (CPAGrip)
    elif query.data == "open_tasks":
        completed = u_info.get('completed_tasks', [])
        if len(completed) >= 3:
            msg = "⚠️ <b>ওয়ার্নিং:</b> আপনার আজকের সব কাজ শেষ। পরবর্তী অফারের জন্য অপেক্ষা করুন।"
            kb = [[InlineKeyboardButton("🔙 Back", callback_data="back_main")]]
        else:
            msg = "🎯 <b>My Offers (CPAGrip)</b>\nঅফারগুলো শেষ করে ডন বাটনে চাপ দিন:"
            kb = []
            for i in range(1, 4):
                tid = f"task{i}"
                if tid not in completed:
                    kb.append([InlineKeyboardButton(f"💎 Offer {i}", url=TASK_LINKS[tid])])
                    kb.append([InlineKeyboardButton(f"🔘 Done {i}", callback_data=f"done_{tid}")])
            kb.append([InlineKeyboardButton("🔙 Back", callback_data="back_main")])
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

    # ৩. CPAGrip Done Verify
    elif query.data.startswith("done_"):
        tid = query.data.replace("done_", "")
        completed = u_info.get('completed_tasks', [])
        if tid not in completed:
            completed.append(tid)
            user_ref.child(user_id).update({'coins': u_info.get('coins', 0) + 200, 'completed_tasks': completed})
            await query.answer("🎉 ২০০ কয়েন যোগ হয়েছে!", show_alert=True)
            await show_main_menu(update, context)

    # ৪. Daily Bonus (Monetag)
    elif query.data == "claim_bonus":
        today = datetime.now().strftime("%Y-%m-%d")
        if u_info.get('last_bonus') == today:
            await query.answer("❌ আজ বোনাস নেওয়া হয়ে গেছে!", show_alert=True)
        else:
            msg = "🎁 ডেইলি বোনাস পেতে নিচের বিজ্ঞাপনটি দেখুন:"
            kb = [[InlineKeyboardButton("📺 Watch Ad (Monetag)", url=MONETAG_SDK_LINK)],
                  [InlineKeyboardButton("✅ Claim 50 Coins", callback_data="verify_bonus")]]
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

    elif query.data == "verify_bonus":
        today = datetime.now().strftime("%Y-%m-%d")
        user_ref.child(user_id).update({'coins': u_info.get('coins', 0) + 50, 'last_bonus': today})
        await query.answer("🎉 ৫০ কয়েন বোনাস পেয়েছেন!", show_alert=True)
        await show_main_menu(update, context)

    # ৫. Wallet & Withdraw
    elif query.data == "open_wallet":
        coins = u_info.get('coins', 0)
        msg = f"💰 <b>Wallet</b>\n\n🪙 Coins: {coins}\n💵 Cash: {coins*0.05:.2f} TK"
        kb = [[InlineKeyboardButton("💳 Withdraw", callback_data="req_withdraw")],
              [InlineKeyboardButton("🔙 Back", callback_data="back_main")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

    elif query.data == "req_withdraw":
        if u_info.get('coins', 0) < 2000:
            await query.answer("❌ নূন্যতম ২০০০ কয়েন প্রয়োজন!", show_alert=True)
        else:
            await query.edit_message_text("📩 পেমেন্ট নিতে আপনার বিকাশ/নগদ নম্বর লিখে পাঠান।")

    elif query.data in ["check_join", "back_main"]:
        await show_main_menu(update, context)

# --- স্টার্ট কমান্ড (রেফারেল লজিকসহ) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    is_new = not user_ref.child(user_id).get()
    if is_new:
        args = context.args
        ref_by = args[0] if args else None
        user_ref.child(user_id).set({'referrals': 0, 'coins': 0, 'completed_tasks': [], 'last_bonus': "", 'ref_by': ref_by})
        if ref_by and ref_by != user_id:
            r_data = user_ref.child(ref_by).get() or {'referrals': 0, 'coins': 0}
            user_ref.child(ref_by).update({'referrals': r_data.get('referrals', 0) + 1, 'coins': r_data.get('coins', 0) + 100})
            try: await context.bot.send_message(chat_id=ref_by, text="🎉 নতুন রেফারেল! ১০০ কয়েন যোগ হয়েছে।")
            except: pass
    await show_main_menu(update, context)

# --- এডমিন কমান্ড: রিসেট ---
async def reset_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        users = user_ref.get()
        if users:
            for uid in users: user_ref.child(uid).update({'completed_tasks': []})
            await update.message.reply_text("✅ সব ইউজারের টাস্ক রিসেট সফল!")

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("resetall", reset_all))
    app_bot.add_handler(CallbackQueryHandler(button_handler))
    print("Bot is running...")
    app_bot.run_polling()
    
