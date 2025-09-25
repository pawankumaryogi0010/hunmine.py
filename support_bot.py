# HUNMINE.py
import logging
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler, 
    ConversationHandler, filters, ContextTypes,
)

# ==============================
# 🔑 Bot Credentials (EDIT HERE)
# ==============================
TOKEN = os.environ.get("TOKEN", "8254092603:AAFcDLevyjKdl9p-GUz71K_NtwgH8MeWoGs")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8241041976"))

# ==============================
# ---------------- STATES ----------------
LANGUAGE, NAME, EMAIL, ISSUE, SUBISSUE = range(5)

# ---------------- STORAGE ----------------
user_data_store = {}
waiting_users = []
active_user = None

# ---------------- LOGGER ----------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------------- HELPERS ----------------
def make_end_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🚪 End Chat", callback_data="end_chat")]])

async def send_admin_summary_for_user(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    data = user_data_store.get(user_id, {})
    summary_text = (
        f"📩 *New Support Request*\n\n"
        f"🌐 Language: {data.get('language', 'N/A')}\n"
        f"👤 Name: {data.get('name', 'N/A')}\n"
        f"📧 Email: {data.get('email', 'N/A')}\n"
        f"📌 Issue: {data.get('issue', 'N/A')}\n"
        f"🔎 Sub-Issue: {data.get('sub_issue', 'N/A')}\n\n"
        f"🆔 User Chat ID: {user_id}"
    )
    await context.bot.send_message(
        chat_id=ADMIN_ID, 
        text=summary_text, 
        reply_markup=make_end_button(), 
        parse_mode="Markdown"
    )

async def notify_user_connected(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    premium_text = (
        "🤝 *You are now securely connected with a HUNMINE Support Specialist.*\n\n"
        "⚡ Our specialist will respond shortly — thank you for your patience."
    )
    await context.bot.send_message(chat_id=user_id, text=premium_text, parse_mode="Markdown")

async def try_connect_next_user(context: ContextTypes.DEFAULT_TYPE):
    global active_user
    if active_user is None and waiting_users:
        next_user = waiting_users.pop(0)
        active_user = next_user
        await send_admin_summary_for_user(context, next_user)
        await notify_user_connected(context, next_user)

# ---------------- HANDLERS ----------------
# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    user_data_store[user_id] = {}
    
    keyboard = [
        [InlineKeyboardButton("English", callback_data="English"), 
         InlineKeyboardButton("हिन्दी", callback_data="Hindi")]
    ]
    welcome = (
        "✨ *Welcome to HUNMINE Official Support* ✨\n\n"
        "🤝 Your trusted gateway for quick and reliable assistance.\n"
        "💡 Experience *Fast, Secure & Hassle-Free* support — because your peace of mind comes first. 🚀\n\n"
        "Please choose your language:"
    )
    
    if update.message:
        await update.message.reply_text(
            welcome, 
            reply_markup=InlineKeyboardMarkup(keyboard), 
            parse_mode="Markdown"
        )
    else:
        await update.callback_query.message.reply_text(
            welcome, 
            reply_markup=InlineKeyboardMarkup(keyboard), 
            parse_mode="Markdown"
        )
    
    return LANGUAGE

# Language chosen
async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = query.data
    user_data_store.setdefault(user_id, {})["language"] = lang
    
    # Edit the original message instead of sending a new one
    await query.edit_message_text(
        text=f"✅ *Language selected:* {lang}\n\n✍️ *Please enter your full name:*", 
        parse_mode="Markdown"
    )
    return NAME

# Name entered
async def set_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.message.text.strip()
    user_data_store.setdefault(user_id, {})["name"] = name
    
    await update.message.reply_text(f"✅ *Name saved:* {name}", parse_mode="Markdown")
    await update.message.reply_text("📧 *Please enter your Email address:*", parse_mode="Markdown")
    return EMAIL

# Email entered
async def set_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    email = update.message.text.strip()
    user_data_store.setdefault(user_id, {})["email"] = email
    
    await update.message.reply_text(f"✅ *Email saved:* {email}", parse_mode="Markdown")
    
    refined_intro = (
        "📂 *HUNMINE Support Assistant*\n\n"
        "To help us serve you better and provide the *fastest possible resolution*, kindly choose the *category that best represents your concern*.\n\n"
        "💡 *Selecting the most accurate category ensures your request is routed instantly to the right specialist, leading to faster and more precise assistance.*"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔑 Login Issue", callback_data="Login Issue")],
        [InlineKeyboardButton("⛏ Mining Related Issue", callback_data="Mining Related Issue")],
        [InlineKeyboardButton("✅ Task Related Issue", callback_data="Task Related Issue")],
        [InlineKeyboardButton("🤝 Refer and Earn Issue", callback_data="Refer and Earn Issue")],
    ]
    
    await update.message.reply_text(
        refined_intro, 
        parse_mode="Markdown", 
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ISSUE

# Issue selected -> show sub-options
async def issue_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    issue = query.data
    user_data_store.setdefault(user_id, {})["issue"] = issue
    
    header = (
        f"🔎 *You have selected:* *{issue}*\n\n"
        "📌 *Please choose the specific problem you are experiencing within this category.*\n\n"
        "💡 *Selecting the most accurate option helps our support team resolve your issue faster.*"
    )
    
    sub_map = {
        "Login Issue": [
            "Verify link not received", 
            "Invalid credentials", 
            "Account locked", 
            "Other login problem"
        ],
        "Mining Related Issue": [
            "Mining not starting", 
            "Rewards missing", 
            "App crash", 
            "Other mining problem"
        ],
        "Task Related Issue": [
            "Task not showing", 
            "Task not verified", 
            "Points missing", 
            "Other task problem"
        ],
        "Refer and Earn Issue": [
            "Refer count issue", 
            "Refer point issue", 
            "Refer signup issue",
            "Other refer problem"
        ],
    }
    
    opts = sub_map.get(issue, ["General Issue"])
    buttons = [[InlineKeyboardButton(text=o, callback_data=f"sub::{o}")] for o in opts]
    
    # Edit the original message instead of sending a new one
    await query.edit_message_text(
        text=header, 
        parse_mode="Markdown", 
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return SUBISSUE

# Sub-issue chosen -> summary + queue
async def subissue_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global active_user
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    raw = query.data
    sub = raw.split("sub::", 1)[1] if raw.startswith("sub::") else raw
    user_data_store.setdefault(user_id, {})["sub_issue"] = sub
    
    waiting_message = (
        "📤 *Please wait while we connect you to an available support specialist.*\n"
    )
    await query.edit_message_text(waiting_message, parse_mode="Markdown")
    
    if active_user is None:
        active_user = user_id
        await send_admin_summary_for_user(context, user_id)
        await notify_user_connected(context, user_id)
    else:
        if user_id not in waiting_users:
            waiting_users.append(user_id)
        pos = waiting_users.index(user_id) + 1
        await context.bot.send_message(
            chat_id=user_id, 
            text=f"⏳ *All agents are busy.* You are in queue position *#{pos}*.", 
            parse_mode="Markdown"
        )
    
    return ConversationHandler.END

# Admin presses End Chat
async def end_chat_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global active_user
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != ADMIN_ID:
        await query.edit_message_text("❌ You are not authorized to end this chat.")
        return
    
    if active_user is not None:
        try:
            await context.bot.send_message(
                chat_id=active_user, 
                text="✅ Your chat has been closed by the support specialist. Thank you!"
            )
        except Exception:
            pass
        
        active_user = None
        await try_connect_next_user(context)
        
        if active_user is not None:
            await query.edit_message_text("✅ Chat ended. Next user connected.")
        else:
            await query.edit_message_text("✅ Chat ended. No users in queue.")
    else:
        await query.edit_message_text("❌ No active chat to end.")

# Two-way text message routing
async def message_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global active_user
    sender_id = update.effective_user.id
    text = update.message.text or ""
    
    if sender_id == ADMIN_ID:
        if active_user is None:
            await update.message.reply_text("❌ No active user to reply to.")
            return
        
        await context.bot.send_message(
            chat_id=active_user, 
            text=f"💬 *Support:* {text}", 
            parse_mode="Markdown"
        )
        return
    
    if sender_id == active_user:
        await context.bot.send_message(
            chat_id=ADMIN_ID, 
            text=f"👤 *{update.effective_user.full_name}* ({sender_id}): {text}", 
            parse_mode="Markdown"
        )
        return
    
    if sender_id in waiting_users:
        pos = waiting_users.index(sender_id) + 1
        await update.message.reply_text(f"⏳ You are in queue position #{pos}. Please wait.")
        return
    
    if sender_id not in user_data_store or "sub_issue" not in user_data_store.get(sender_id, {}):
        await update.message.reply_text("✳️ Please start with /start to create a support request.")
        return
    
    if active_user is None and sender_id not in waiting_users:
        waiting_users.append(sender_id)
        await update.message.reply_text(f"⏳ You are added to queue position #{waiting_users.index(sender_id)+1}. Please wait.")
        await try_connect_next_user(context)
        return
    
    await update.message.reply_text("⏳ Please wait while we connect you to support.")

# File/Photo routing
async def file_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global active_user
    sender_id = update.effective_user.id
    
    file_obj = update.message.document or (update.message.photo[-1] if update.message.photo else None)
    if file_obj is None:
        await update.message.reply_text("⚠️ No valid file detected. Please send a photo or document.")
        return
    
    if sender_id == ADMIN_ID:
        if active_user is None:
            await update.message.reply_text("❌ No active user to send file to.")
            return
        
        if update.message.photo:
            await context.bot.send_photo(
                chat_id=active_user, 
                photo=file_obj.file_id, 
                caption="💬 Support sent a photo"
            )
        else:
            await context.bot.send_document(
                chat_id=active_user, 
                document=file_obj.file_id, 
                caption="💬 Support sent a file"
            )
        return
    
    if sender_id == active_user:
        if update.message.photo:
            await context.bot.send_photo(
                chat_id=ADMIN_ID, 
                photo=file_obj.file_id, 
                caption=f"📷 From {update.effective_user.full_name} ({sender_id})"
            )
        else:
            await context.bot.send_document(
                chat_id=ADMIN_ID, 
                document=file_obj.file_id, 
                caption=f"📎 From {update.effective_user.full_name} ({sender_id})"
            )
        await update.message.reply_text("✅ File forwarded to support.")
        return
    
    if sender_id in waiting_users:
        pos = waiting_users.index(sender_id) + 1
        await update.message.reply_text(f"⏳ You are in queue position #{pos}. Please wait to upload files when connected.")
        return
    
    await update.message.reply_text("✳️ Please start with /start to create a support request.")

# Cancel handler
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id in waiting_users:
        waiting_users.remove(user_id)
    
    if user_id in user_data_store:
        del user_data_store[user_id]
    
    await update.message.reply_text("❌ Your support request has been cancelled.")
    return ConversationHandler.END

# ---------------- APP SETUP ----------------
def main():
    app = Application.builder().token(TOKEN).build()
    
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [CallbackQueryHandler(set_language, pattern="^(English|Hindi)$")],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_name)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_email)],
            ISSUE: [CallbackQueryHandler(issue_selected, pattern="^(Login Issue|Mining Related Issue|Task Related Issue|Refer and Earn Issue)$")],
            SUBISSUE: [CallbackQueryHandler(subissue_selected, pattern="^sub::.*")]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )
    
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(end_chat_callback, pattern="^end_chat$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_router))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, file_router))
    
    print("🤖 HUNMINE Support Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()