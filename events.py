import random
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from config import GROUP_ID, WORLD_EVENTS, ADMIN_IDS
from db.database import get_active_event, start_world_event, end_expired_events
from systems.stickers import send_sticker

async def check_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return
    end_expired_events()
    event = get_active_event()
    if not event:
        await update.message.reply_text("🌿 The swamp is calm. No active events.")
        return

    ev = WORLD_EVENTS.get(event["event_type"], {})
    ends_in = int(event["ends_at"] - datetime.now().timestamp())
    h, m = ends_in // 3600, (ends_in % 3600) // 60
    await send_sticker(context.bot, GROUP_ID, ev.get("sticker", "shocked"))
    await update.message.reply_text(
        f"🌍 *ACTIVE WORLD EVENT*\n"
        f"━━━━━━━━━━━━━\n"
        f"{ev.get('name', event['event_type'])}\n\n"
        f"_{ev.get('desc', '')}_\n\n"
        f"⚡ XP Multiplier: *×{ev.get('xp_multiplier', 1)}*\n"
        f"⏱ Ends in: *{h}h {m}m*",
        parse_mode="Markdown"
    )

async def announce_random_event(bot, chat_id):
    """Called by scheduler to trigger a random world event."""
    end_expired_events()
    existing = get_active_event()
    if existing:
        return  # Don't stack events

    event_type = random.choice(list(WORLD_EVENTS.keys()))
    ev = WORLD_EVENTS[event_type]
    duration = ev["duration_hours"]
    start_world_event(event_type, duration)

    await send_sticker(bot, chat_id, ev.get("sticker", "shocked"))
    await bot.send_message(
        chat_id=chat_id,
        text=(
            f"⚠️ *WORLD EVENT TRIGGERED*\n"
            f"━━━━━━━━━━━━━\n"
            f"{ev['name']}\n\n"
            f"_{ev['desc']}_\n\n"
            f"⚡ XP Multiplier: *×{ev['xp_multiplier']}*\n"
            f"⏱ Duration: *{duration} hours*\n\n"
            f"_The swamp shifts. Adapt or fall._"
        ),
        parse_mode="Markdown"
    )

async def admin_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command: /admin event <event_type>"""
    if update.effective_user.id not in ADMIN_IDS:
        return

    if not context.args or len(context.args) < 2:
        keys = ", ".join(WORLD_EVENTS.keys())
        await update.message.reply_text(f"Usage: /admin event <type>\nTypes: {keys}")
        return

    event_type = context.args[1].lower().replace(" ", "_")
    if event_type not in WORLD_EVENTS:
        await update.message.reply_text(f"Unknown event type: {event_type}")
        return

    ev = WORLD_EVENTS[event_type]
    start_world_event(event_type, ev["duration_hours"])
    await announce_random_event(context.bot, GROUP_ID)
