import logging
import asyncio
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    BotCommand
)
from telegram.ext import (
    Application, CommandHandler, ContextTypes,
    MessageHandler, filters
)

from config import BOT_TOKEN, WEBHOOK_URL, PORT, GROUP_ID, GROUP_LINK, CA_ADDRESS, START_IMAGE
from db.database import init_db
from keep_alive import keep_alive
from scheduler import setup_scheduler

# ── Handlers ──────────────────────────────────────────────────────────────────
from handlers.hunt import hunt
from handlers.profile import profile, inventory_cmd, leaderboard, factions_cmd
from handlers.social import ambush, protect, revenge, gift, join
from handlers.events import check_event, admin_event
from handlers.admin import admin
from systems.stickers import send_sticker

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── /start (DM only) ──────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type = update.effective_chat.type
    user = update.effective_user

    if chat_type != "private":
        return  # Only respond to DMs

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🐊 Enter the Swamp", url=GROUP_LINK)]
    ])

    caption = (
        f"🐊 *Welcome to CROCO, @{user.first_name}*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"The swamp doesn't sleep.\n\n"
        f"Hunt. Dominate. Survive.\n\n"
        f"🌿 Join the community. Build your legend.\n"
        f"👑 Rank up. Claim territory. Go dark.\n\n"
        f"📋 *CA:* `{CA_ADDRESS}`"
    )

    try:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=START_IMAGE,
            caption=caption,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    except Exception:
        await update.message.reply_text(caption, parse_mode="Markdown", reply_markup=keyboard)

# ── /help ─────────────────────────────────────────────────────────────────────
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return
    text = (
        "🐊 *CROCO COMMANDS*\n"
        "━━━━━━━━━━━━━\n"
        "⚔️ *Survival*\n"
        "/hunt — Hunt every 8 hours\n"
        "/profile — View your stats\n"
        "/inventory — Check your items\n\n"
        "🌿 *Social*\n"
        "/ambush @user — Strike from shadows (12h CD)\n"
        "/protect — Shield yourself 5 hours (24h CD)\n"
        "/revenge — Strike back after ambush\n"
        "/gift @user item — Give an item\n\n"
        "🌍 *Territory*\n"
        "/join <faction> — Join a faction\n"
        "/factions — Faction leaderboard\n\n"
        "📊 *Stats*\n"
        "/leaderboard — Top 10 crocos\n"
        "/event — Check active world event\n\n"
        f"📋 CA: `{CA_ADDRESS}`"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# ── New member greeting ───────────────────────────────────────────────────────
async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return
    for member in update.message.new_chat_members:
        if member.is_bot:
            continue
        await send_sticker(context.bot, GROUP_ID, "hi")
        await update.message.reply_text(
            f"🐊 *@{member.username or member.first_name}* enters the swamp.\n\n"
            f"The reeds part. Eyes watch from the murk.\n"
            f"Start with /hunt to mark your territory.\n"
            f"Pick your side with /join <faction>.\n\n"
            f"_Welcome to the dark._",
            parse_mode="Markdown"
        )

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    # Init DB
    init_db()

    # Keep alive (UptimeRobot compatible)
    keep_alive()

    # Build application
    app = Application.builder().token(BOT_TOKEN).build()

    # Register commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("hunt", hunt))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("inventory", inventory_cmd))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("factions", factions_cmd))
    app.add_handler(CommandHandler("ambush", ambush))
    app.add_handler(CommandHandler("protect", protect))
    app.add_handler(CommandHandler("revenge", revenge))
    app.add_handler(CommandHandler("gift", gift))
    app.add_handler(CommandHandler("join", join))
    app.add_handler(CommandHandler("event", check_event))
    app.add_handler(CommandHandler("admin", admin))

    # New member welcome
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member))

    # Setup scheduler with bot reference
    setup_scheduler(app.bot)

    # Set bot commands for Telegram menu
    async def post_init(application):
        await application.bot.set_my_commands([
            BotCommand("hunt", "Hunt every 8 hours"),
            BotCommand("profile", "View your croco profile"),
            BotCommand("inventory", "Check your items"),
            BotCommand("leaderboard", "Top 10 crocos"),
            BotCommand("factions", "Faction standings"),
            BotCommand("ambush", "Ambush another croco"),
            BotCommand("protect", "Activate swamp shield"),
            BotCommand("revenge", "Take revenge on attacker"),
            BotCommand("gift", "Gift an item to ally"),
            BotCommand("join", "Join a faction"),
            BotCommand("event", "Check active world event"),
            BotCommand("help", "All commands"),
        ])

    app.post_init = post_init

    logger.info("🐊 CrocoBot starting with webhook...")

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=f"{WEBHOOK_URL}/webhook",
        url_path="/webhook",
        drop_pending_updates=True,
    )

if __name__ == "__main__":
    main()
