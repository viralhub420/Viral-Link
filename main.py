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

# --- ১. ওয়েব সার্ভার (মিনি অ্যাপের জন্য) ---
@app.route('/')
def home():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Error: index.html ফাইলটি পাওয়া যায়নি!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# --- ২. কনফিগারেশন ---
BOT_TOKEN =  
ADMIN_ID = 6311806060 
CHANNEL_USERNAME = "@viralmoviehubbd"
FIREBASE_DB_URL = "https://viralmoviehubbd-default-rtdb.firebaseio.com/"
RAILWAY_APP_URL = "https://viral-link-production.up.railway.app" 
ADS_URL = "https://viralhub420.github.io/Viral-Link/ads.html"

TASK_LINKS = {
    "task1": "https://singingfiles.com/show.php?l=0&u=2499908&id=54747", 
    "task2": "https://singingfiles.com/show.php?l=0&u=2499908&id=36521",
    "task3": "https://singingfiles.com/show.php?l=0&u=2499908&id=54746"
}

# ফায়ারবেস ইনিশিয়াল
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_DB_URL})
    except Exception as e:
        print(f"Firebase Error: {e}")

user_ref = db.reference('users')
movie_ref = db.reference('movies')

# --- ৩. সাহায্যকারী ও ব্রডকাস্ট লজিক ---
async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

def get_progress_bar(count, total=5):
    filled = "█" * min(count, total)
    empty = "░" * max(0, total - count)
    return f"[{filled}{empty}] {int((min(count, total)/total)*100)}%"

async def send_to_all(bot, text):
    all_users = user_ref.get()
    if not all_users: return 0, 0
    s, f = 0, 0
    for uid in all_users.keys():
        try:
            await bot.send_message(chat_id=uid, text=text, parse_mode=ParseMode.HTML)
            s += 1
            await asyncio.sleep(0.05)
        except: f += 1
    return s, f

# --- ৪. এডমিন কমান্ডস (নতুন ফিচার) ---
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    all_users = user_ref.get()
    count = len(all_users) if all_users else 0
    await update.message.reply_text(f"📊 <b>মোট ইউজার:</b> {count} জন", parse_mode=ParseMode.HTML)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not context.args:
        await update.message.reply_text("❌ লিখুন: `/broadcast আপনার মেসেজ`")
        return
    msg = "📢 <b>গুরুত্বপূর্ণ নোটিশ:</b>\n\n" + " ".join(context.args)
    status = await update.message.reply_text("🚀 পাঠানো হচ্ছে...")
    s, f = await send_to_all(context.bot, msg)
    await status.edit_text(f"✅ সম্পন্ন!\n🟢 সফল: {s}\n🔴 ব্যর্থ: {f}")

# --- ৫. আপনার অরিজিনাল ফাংশনগুলো (অপরিবর্তিত) ---
async def post_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        text = update.message.text.replace("/post", "").strip()
        parts = text.split("|")
        if len(parts) != 3:
            await update.message.reply_text("⚠️ ফরম্যাট: /post নাম | ছবি লিঙ্ক | ভিডিও লিঙ্ক")
            return
        title, img, url = parts[0].strip(), parts[1].strip(), parts[2].strip()
        movie_ref.push({'title': title, 'image_url': img, 'video_url': url, 'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        await update.message.reply_text(f"✅ '{title}' সেভ হয়েছে!")
        # অটো নোটিফিকেশন
        await send_to_all(context.bot, f"🎬 <b>নতুন মুভি এসেছে!</b>\n\n🎥 নাম: {title}\n\nএখনই অ্যাপে দেখুন।")
    except Exception as e: await update.message.reply_text(f"Error: {e}")

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

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(update.effective_user.id)
    u_info = user_ref.child(user_id).get() or {'referrals': 0, 'coins': 0, 'completed_tasks': []}
    
    if query.data == "open_app":
        referrals = u_info.get('referrals', 0)
        if referrals < 5:
            bot_info = await context.bot.get_me()
            ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
            msg = f"🔒 <b>লক!</b> মুভি দেখতে ৫ জন বন্ধুকে ইনভাইট করুন।\n\n📊 {get_progress_bar(referrals)}\n🔗 <code>{ref_link}</code>"
            kb = [[InlineKeyboardButton("🚀 Invite Friends", switch_inline_query=f"\nমুভি দেখো!\n{ref_link}")],
                  [InlineKeyboardButton("🔙 Back", callback_data="back_main")]]
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
        else:
            kb = [[InlineKeyboardButton("📺 Watch Ad to Unlock", url=ADS_URL)],
                  [InlineKeyboardButton("🎬 Open Movie App", web_app={"url": RAILWAY_APP_URL})]]
            await query.edit_message_text("✅ অ্যাডটি দেখে 'Open App' এ ক্লিক করুন।", reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

    elif query.data == "open_tasks":
        completed = u_info.get('completed_tasks', [])
        kb = []
        for i in range(1, 4):
            tid = f"task{i}"
            if tid not in completed:
                kb.append([InlineKeyboardButton(f"💎 Offer {i}", url=TASK_LINKS[tid])])
                kb.append([InlineKeyboardButton(f"🔘 Done {i}", callback_data=f"done_{tid}")])
        kb.append([InlineKeyboardButton("🔙 Back", callback_data="back_main")])
        await query.edit_message_text("🎯 <b>My Offers:</b>", reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

    elif query.data.startswith("done_"):
        tid = query.data.replace("done_", "")
        completed = u_info.get('completed_tasks', [])
        if tid not in completed:
            completed.append(tid)
            user_ref.child(user_id).update({'coins': u_info.get('coins', 0) + 200, 'completed_tasks': completed})
            await query.answer("🎉 ২০০ কয়েন যোগ হয়েছে!", show_alert=True)
            await show_main_menu(update, context)

    elif query.data == "claim_bonus":
        kb = [[InlineKeyboardButton("📺 Watch Ad (10 🪙)", url=ADS_URL)],
              [InlineKeyboardButton("✅ Claim Reward", callback_data="verify_bonus")],
              [InlineKeyboardButton("🔙 Back", callback_data="back_main")]]
        await query.edit_message_text("🎁 <b>Viral Reward Center</b>", reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

    elif query.data == "verify_bonus":
        user_ref.child(user_id).update({'coins': u_info.get('coins', 0) + 10})
        await query.answer("📺 ১০ কয়েন যোগ হয়েছে।", show_alert=True)

    elif query.data == "open_referral":
        bot_info = await context.bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
        msg = f"🚀 <b>Invite & Earn</b>\n\nপ্রতিটি রেফারে ১০০ কয়েন।\n🔗 <code>{ref_link}</code>"
        kb = [[InlineKeyboardButton("📢 Share Link", switch_inline_query=f"\nমুভি দেখো!\n{ref_link}")],
              [InlineKeyboardButton("🔙 Back", callback_data="back_main")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

    elif query.data == "open_wallet":
        coins = u_info.get('coins', 0)
        msg = f"💰 <b>Wallet</b>\n🪙 Coins: {coins}\n💵 Cash: {coins*0.05:.2f} TK"
        kb = [[InlineKeyboardButton("💳 Withdraw Now", callback_data="req_withdraw")],
              [InlineKeyboardButton("🔙 Back", callback_data="back_main")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

    elif query.data == "req_withdraw":
        if u_info.get('coins', 0) < 2000:
            await query.answer("❌ কমপক্ষে ২০০০ কয়েন লাগবে!", show_alert=True)
        else:
            context.user_data['awaiting_num'] = True
            await query.edit_message_text("📩 আপনার বিকাশ/নগদ নম্বরটি লিখুন:")

    elif query.data in ["back_main", "check_join"]:
        await show_main_menu(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if context.user_data.get('awaiting_num'):
        num = update.message.text
        coins = user_ref.child(user_id).get().get('coins', 0)
        await context.bot.send_message(ADMIN_ID, f"💳 <b>Withdraw!</b>\nID: {user_id}\nCoins: {coins}\nNo: {num}")
        user_ref.child(user_id).update({'coins': 0})
        context.user_data['awaiting_num'] = False
        await update.message.reply_text("✅ রিকোয়েস্ট পাঠানো হয়েছে।")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not user_ref.child(user_id).get():
        ref_by = context.args[0] if context.args else None
        user_ref.child(user_id).set({'referrals': 0, 'coins': 0, 'completed_tasks': [], 'ref_by': ref_by})
        if ref_by and ref_by != user_id:
            r = user_ref.child(ref_by).get() or {'referrals': 0, 'coins': 0}
            user_ref.child(ref_by).update({'referrals': r.get('referrals', 0)+1, 'coins': r.get('coins', 0)+100})
    await show_main_menu(update, context)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot = ApplicationBuilder().token(BOT_TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("stats", stats))
    bot.add_handler(CommandHandler("broadcast", broadcast))
    bot.add_handler(CommandHandler("post", post_movie))
    bot.add_handler(CallbackQueryHandler(button_handler))
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot started!")
    bot.run_polling()
        
