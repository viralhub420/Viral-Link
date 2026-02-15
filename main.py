import os
import threading
import time
import hashlib
from flask import Flask
import firebase_admin
from firebase_admin import credentials, db
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    WebAppInfo
)
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from datetime import datetime

# ---------------- FLASK ----------------
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Live!"

@app.route('/admin')
def admin_panel():
    users = user_ref.get() or {}
    total_users = len(users)
    total_coins = sum(u.get("coins", 0) for u in users.values())
    pending = sum(1 for u in users.values() if u.get("withdraw_status") == "pending")

    return f"""
    <h1>Admin Dashboard</h1>
    <p>Total Users: {total_users}</p>
    <p>Total Coins: {total_coins}</p>
    <p>Pending Withdraw: {pending}</p>
    """

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

# ---------------- CONFIG ----------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
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

# ---------------- FIREBASE ----------------
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_DB_URL})

user_ref = db.reference('users')

# ---------------- HELPERS ----------------
async def is_subscribed(bot, user_id: int):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

def progress_bar(count, total=5):
    return f"[{'█'*count}{'░'*(total-count)}] {int((count/total)*100)}%"

def generate_ad_token(user_id):
    token = hashlib.sha256(f"{user_id}{time.time()}".encode()).hexdigest()
    user_ref.child(str(user_id)).update({
        "ad_token": token,
        "ad_time": time.time()
    })
    return token

# ---------------- MAIN MENU ----------------
async def show_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await is_subscribed(context.bot, user_id):
        kb = [
            [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton("✅ Joined", callback_data="check_join")]
        ]
        msg = "❌ <b>Join Channel First!</b>"
    else:
        kb = [
            [InlineKeyboardButton("🚀 Open Movie App", callback_data="open_app")],
            [InlineKeyboardButton("🎁 Offers", callback_data="offers")],
            [InlineKeyboardButton("🚀 Referral", callback_data="referral")],
            [InlineKeyboardButton("📅 Daily Bonus", callback_data="bonus")],
            [InlineKeyboardButton("💰 Wallet", callback_data="wallet")]
        ]
        msg = "🎬 <b>Viral Movie Hub</b>"

    target = update.callback_query.message if update.callback_query else update.message
    await target.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

# ---------------- BUTTON HANDLER ----------------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    user_key = str(user_id)
    data = user_ref.child(user_key).get() or {}

    # OPEN APP
    if query.data == "open_app":
        refs = data.get("referrals", 0)
        if refs < 5:
            bot_info = await context.bot.get_me()
            link = f"https://t.me/{bot_info.username}?start={user_id}"
            msg = f"🔒 Invite 5 Friends\n\n{progress_bar(min(refs,5))}\n<code>{link}</code>"
            kb = [[InlineKeyboardButton("📢 Invite", switch_inline_query=link)]]
        else:
            msg = "Watch Ad then Open App"
            kb = [
                [InlineKeyboardButton("📺 Watch Ad", url=ADS_URL)],
                [InlineKeyboardButton("🎬 Open App", web_app=WebAppInfo(url=GITHUB_PAGES_URL))]
            ]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

    # WALLET
    elif query.data == "wallet":
        coins = data.get("coins",0)
        msg = f"🪙 Coins: {coins}\n💵 Cash: {coins*0.05:.2f} TK"
        kb = [[InlineKeyboardButton("💳 Withdraw", callback_data="withdraw")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))

# WITHDRAW
    elif query.data == "withdraw":
        if data.get("coins",0) < 2000:
            await query.answer("Minimum 2000 coins!", show_alert=True)
        elif data.get("withdraw_status") == "pending":
            await query.answer("Already pending!", show_alert=True)
        else:
            context.user_data["awaiting_number"] = True
            await query.edit_message_text("Send your bKash/Nagad number:")

    elif query.data.startswith("paid_"):
        target = query.data.split("_")[1]
        tdata = user_ref.child(target).get()
        if tdata and tdata.get("withdraw_status") == "pending":
            user_ref.child(target).update({"coins":0,"withdraw_status":"paid"})
            await context.bot.send_message(int(target),"✅ Payment Completed!")
            await query.edit_message_text("Payment Done.")

    elif query.data in ["check_join"]:
        await show_main(update, context)

# ---------------- MESSAGE HANDLER ----------------
async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_key = str(user_id)

    if context.user_data.get("awaiting_number"):
        number = update.message.text
        data = user_ref.child(user_key).get()

        user_ref.child(user_key).update({"withdraw_status":"pending"})

        kb = [[InlineKeyboardButton("✅ Mark Paid", callback_data=f"paid_{user_key}")]]

        await context.bot.send_message(
            ADMIN_ID,
            f"Withdraw Request\nID:{user_id}\nCoins:{data.get('coins',0)}\nNumber:{number}",
            reply_markup=InlineKeyboardMarkup(kb)
        )

        context.user_data["awaiting_number"] = False
        await update.message.reply_text("Request Sent!")

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_key = str(user_id)

    if not user_ref.child(user_key).get():
        args = context.args
        ref = args[0] if args and args[0] != user_key else None

        user_ref.child(user_key).set({
            "coins":0,
            "referrals":0,
            "completed_tasks":[],
            "last_bonus":"",
            "withdraw_status":"",
            "ref_by":ref
        })

        if ref:
            rdata = user_ref.child(ref).get()
            if rdata:
                user_ref.child(ref).update({
                    "referrals": rdata.get("referrals",0)+1,
                    "coins": rdata.get("coins",0)+100
                })

    await show_main(update, context)

# ---------------- RUN ----------------
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()

    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(button))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message))

    print("Bot Running...")
    app_bot.run_polling()
