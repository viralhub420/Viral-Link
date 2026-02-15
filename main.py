import os
import asyncio
import threading
from flask import Flask
import firebase_admin
from firebase_admin import credentials, db
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from datetime import datetime

app = Flask(__name__)
@app.route('/')
def home(): return "Bot is live!"
def run_flask(): app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

# --- ১. কনফিগারেশন ---
BOT_TOKEN = "8595737059:AAE8yY_qdUskQg1rPXCBaUejQbX79pJTkuM" 
ADMIN_ID = 6311806060 
CHANNEL_USERNAME = "@viralmoviehubbd"
FIREBASE_DB_URL = "https://viralmoviehubbd-default-rtdb.firebaseio.com/"
GITHUB_PAGES_URL = "https://viralhub420.github.io/Viral-Link/"
ADS_URL = "https://viralhub420.github.io/Viral-Link/ads.html"

TASK_LINKS = {
    "task1": "https://singingfiles.com/show.php?l=0&u=2499908&id=54747", 
    "task2": "https://singingfiles.com/show.php?l=0&u=2499908&id=36521",
    "task3": "https://singingfiles.com/show.php?l=0&u=2499908&id=54746"
}

if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_DB_URL})

user_ref = db.reference('users')

# --- ২. সাহায্যকারী ফাংশন ---
async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

def get_progress_bar(count, total=5):
    filled = "█" * count
    empty = "░" * (total - count)
    return f"[{filled}{empty}] {int((count/total)*100)}%"

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
            [InlineKeyboardButton("🚀 Referral Reward", callback_data="open_referral")],
            [InlineKeyboardButton("📅 Daily Bonus & Rewards", callback_data="claim_bonus")],
            [InlineKeyboardButton("💰 Wallet & Withdraw", callback_data="open_wallet")]
        ]
    target = update.callback_query.message if update.callback_query else update.message
    await target.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

# --- ৩. বাটন হ্যান্ডলার (সব লজিক এখানে) ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(update.effective_user.id)
    u_info = user_ref.child(user_id).get() or {'referrals': 0, 'coins': 0, 'completed_tasks': []}
    
    # ১. মুভি অ্যাপ ওপেন
    if query.data == "open_app":
        referrals = u_info.get('referrals', 0)
        if referrals < 5:
            bot_info = await context.bot.get_me()
            ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
            msg = f"🔒 <b>লক!</b> মুভি দেখতে ৫ জন বন্ধুকে ইনভাইট করুন।\n\n📊 {get_progress_bar(min(referrals, 5))}\n🔗 <code>{ref_link}</code>"
            kb = [[InlineKeyboardButton("🚀 Invite Friends", switch_inline_query=f"\nমুভি দেখো!\n{ref_link}")],
                  [InlineKeyboardButton("🔙 Back", callback_data="back_main")]]
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
        else:
            msg = "✅ অ্যাডটি দেখে 'Open App' এ ক্লিক করুন।"
            kb = [[InlineKeyboardButton("📺 Watch Ad to Unlock", url=ADS_URL)],
                  [InlineKeyboardButton("🎬 Open Movie App", web_app={"url": GITHUB_PAGES_URL})]]
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

    # ২. মাই অফারস
    elif query.data == "open_tasks":
        completed = u_info.get('completed_tasks', [])
        kb = []
        for i in range(1, 4):
            tid = f"task{i}"
            if tid not in completed:
                kb.append([InlineKeyboardButton(f"💎 Offer {i}", url=TASK_LINKS[tid])])
                kb.append([InlineKeyboardButton(f"🔘 Done {i}", callback_data=f"done_{tid}")])
        kb.append([InlineKeyboardButton("🔙 Back", callback_data="back_main")])
        await query.edit_message_text("🎯 <b>My Offers:</b> অফার পূরণ করে 'Done' ক্লিক করুন।", reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

    elif query.data.startswith("done_"):
        tid = query.data.replace("done_", "")
        completed = u_info.get('completed_tasks', [])
        if tid not in completed:
            completed.append(tid)
            user_ref.child(user_id).update({'coins': u_info.get('coins', 0) + 200, 'completed_tasks': completed})
            await query.answer("🎉 ২০০ কয়েন যোগ হয়েছে!", show_alert=True)
            await show_main_menu(update, context)

    # ৩. বোনাস সেন্টার
    elif query.data == "claim_bonus":
        msg = "🎁 <b>রিওয়ার্ড সেন্টার:</b> অ্যাড দেখে পয়েন্ট নিন!"
        kb = [[InlineKeyboardButton("📺 Watch Ad (50 🪙)", url=ADS_URL)],
              [InlineKeyboardButton("✅ Claim Bonus", callback_data="verify_bonus")],
              [InlineKeyboardButton("🔙 Back", callback_data="back_main")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

    elif query.data == "verify_bonus":
        today = datetime.now().strftime("%Y-%m-%d")
        if u_info.get('last_bonus') == today:
            await query.answer("❌ আজ অলরেডি নিয়েছেন!", show_alert=True)
        else:
            user_ref.child(user_id).update({'coins': u_info.get('coins', 0) + 50, 'last_bonus': today})
            await query.answer("🎉 ৫০ কয়েন যোগ হয়েছে!", show_alert=True)
            await show_main_menu(update, context)

    # ৪. রেফারেল
    elif query.data == "open_referral":
        bot_info = await context.bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
        msg = f"🚀 <b>Invite & Earn</b>\n\nপ্রতিটি রেফারে ১০০ কয়েন।\n\n🔗 <code>{ref_link}</code>"
        kb = [[InlineKeyboardButton("📢 Share Link", switch_inline_query=f"\nমুভি দেখো!\n{ref_link}")],
              [InlineKeyboardButton("🔙 Back", callback_data="back_main")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

    # ৫. ওয়ালেট ও উইথড্র
    elif query.data == "open_wallet":
        coins = u_info.get('coins', 0)
        msg = f"💰 <b>Your Wallet</b>\n\n🪙 Coins: {coins}\n💵 Cash: {coins*0.05:.2f} TK"
        kb = [[InlineKeyboardButton("💳 Withdraw Now", callback_data="req_withdraw")],
              [InlineKeyboardButton("🔙 Back", callback_data="back_main")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

    elif query.data == "req_withdraw":
        if u_info.get('coins', 0) < 2000:
            await query.answer("❌ নূন্যতম ২০০০ কয়েন প্রয়োজন!", show_alert=True)
        else:
            context.user_data['awaiting_num'] = True
            await query.edit_message_text("📩 পেমেন্ট নিতে আপনার <b>বিকাশ/নগদ নম্বর</b> লিখে পাঠান।")

    elif query.data.startswith("paid_"):
        target_id = query.data.replace("paid_", "")
        try:
            await context.bot.send_message(chat_id=target_id, text="🎉 <b>অভিনন্দন!</b>\nআপনার উইথড্র পেমেন্ট সফল হয়েছে।")
            await query.edit_message_text(f"✅ <b>পেমেন্ট সাকসেসফুল!</b>\nআইডি: {target_id}")
            await query.answer("✅ সম্পন্ন!", show_alert=True)
        except: pass

    elif query.data in ["back_main", "check_join"]:
        await show_main_menu(update, context)

# --- ৪. মেসেজ ও স্টার্ট ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if context.user_data.get('awaiting_num'):
        number = update.message.text
        u_info = user_ref.child(user_id).get()
        admin_text = f"💳 <b>Withdraw Request!</b>\n👤 ID: {user_id}\n💰 Coins: {u_info['coins']}\n📱 No: {number}"
        kb = [[InlineKeyboardButton("✅ Mark as Paid", callback_data=f"paid_{user_id}")]]
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
        user_ref.child(user_id).update({'coins': 0})
        context.user_data['awaiting_num'] = False
        await update.message.reply_text("✅ রিকোয়েস্ট পাঠানো হয়েছে।")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    is_new = not user_ref.child(user_id).get()
    if is_new:
        args = context.args
        ref_by = args[0] if args and args[0] != user_id else None
        user_ref.child(user_id).set({'referrals': 0, 'coins': 0, 'completed_tasks': [], 'last_bonus': "", 'ref_by': ref_by})
        if ref_by:
            r_data = user_ref.child(ref_by).get() or {'referrals': 0, 'coins': 0}
            user_ref.child(ref_by).update({'referrals': r_data.get('referrals', 0) + 1, 'coins': r_data.get('coins', 0) + 100})
    await show_main_menu(update, context)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(button_handler))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot is ready!")
    app_bot.run_polling()
