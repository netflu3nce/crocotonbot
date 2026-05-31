import sys
import os
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import tornado.web

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import BOT_TOKEN, WEBHOOK_URL, PORT, GROUP_ID, GROUP_LINK, CA_ADDRESS, ADMIN_IDS
from db.database import init_db
from scheduler import setup_scheduler, scheduler
from handlers.hunt import hunt
from handlers.profile import profile, inventory_cmd, leaderboard, factions_cmd
from handlers.social import ambush, protect, revenge, gift, join
from handlers.events import check_event
from handlers.admin import admin
from systems.stickers import send_sticker

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🐊 Enter the Swamp", url=GROUP_LINK)]
    ])
    caption = (
        f"*Welcome to CROCO, {update.effective_user.first_name}*\n"
        f"━━━━━━━━━━━━━\n"
        f"The swamp doesn't sleep.\n\n"
        f"Hunt. Dominate. Survive.\n\n"
        f"Join the community. Build your legend.\n"
        f"Rank up. Claim territory. Go dark.\n\n"
        f"*CA:* `{CA_ADDRESS}`"
    )
    try:
        from config import START_IMAGE
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=START_IMAGE,
            caption=caption,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    except Exception:
        await update.effective_chat.send_message(caption, parse_mode="Markdown", reply_markup=keyboard)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return
    text = (
        "🐊 *CROCO COMMANDS*\n"
        "━━━━━━━━━━━━━\n"
        "*Survival*\n"
        "/hunt — Hunt every 8 hours\n"
        "/profile — View your stats\n"
        "/inventory — Check your items\n\n"
        "*Social*\n"
        "/ambush @user — Strike from shadows (12h CD)\n"
        "/protect — Shield yourself 5 hours (24h CD)\n"
        "/revenge — Strike back after ambush\n"
        "/gift @user item — Give an item\n\n"
        "*Territory*\n"
        "/join <faction> — Join a faction\n"
        "/factions — Faction leaderboard\n\n"
        "*Stats*\n"
        "/leaderboard — Top 10 crocos\n"
        "/event — Check active world event\n\n"
        f"CA: `{CA_ADDRESS}`"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return
    for member in update.message.new_chat_members:
        if member.is_bot:
            continue
        await send_sticker(context.bot, GROUP_ID, "hi")
        await update.message.reply_text(
            f"🐊 {member.first_name} enters the swamp.\n\n"
            f"The reeds part. Eyes watch from the murk.\n"
            f"Start with /hunt to mark your territory.\n"
            f"Pick your side with /join <faction>.\n\n"
            f"Welcome to the dark. 🖤",
            parse_mode="Markdown"
        )

async def post_init(application: Application):
    setup_scheduler(application.bot)
    if not scheduler.running:
        scheduler.start()
        
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
        BotCommand("admin", "Admin Terminal"),
    ])
    logger.info("🐊 CrocoBot post init complete.")

class HealthHandler(tornado.web.RequestHandler):
    """GET /health → 200 OK — satisfies Render's health check on the same PORT."""
    def get(self):
        self.set_status(200)
        self.write("OK")

async def main_async():
    init_db()
    
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )
    
    # Handlers Registration
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
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member))
    
    logger.info("🐊 Starting python-telegram-bot internal webhook lifecycle...")
    
    # Initialize application components
    await app.initialize()
    
    # url_path must be non-empty so the root GET "/" is free for the health check.
    # Render pings healthCheckPath=/health (GET), webhook receives POST at /webhook.
    await app.updater.start_webhook(
        listen="0.0.0.0",
        port=int(PORT),
        url_path="webhook",
        webhook_url=f"{WEBHOOK_URL}/webhook",
        drop_pending_updates=True,
    )

    # Register /health on the same Tornado server PTB started.
    # Render's health check hits GET /health on PORT — this satisfies it.
    app.updater.httpd.add_handlers(".*", [(r"/health", HealthHandler)])
    logger.info("🐊 /health route registered on Tornado server.")

    await app.start()
    
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit, asyncio.CancelledError):
        logger.info("Stopping bot engine subsystems gracefully...")
        if scheduler.running:
            scheduler.shutdown()
        await app.stop()
        await app.updater.stop_webhook()
        await app.shutdown()

def main():
    try:
        asyncio.run(main_async())
    except Exception as e:
        logger.critical(f"Fatal Engine Panic crash: {e}", exc_info=True)

if __name__ == "__main__":
    main()
