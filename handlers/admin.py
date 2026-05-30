import random
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from config import GROUP_ID, ADMIN_IDS, WORLD_EVENTS
from db.database import (
    get_ecosystem_stats, get_user, update_user,
    start_world_event, reset_faction_xp, get_conn
)
from systems.stickers import send_sticker

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # Ensure any admin configured inside config.ADMIN_IDS is allowed entry
    if user.id not in ADMIN_IDS:
        return  # Silent ignore

    if not context.args:
        await update.message.reply_text(
            "🛠 *Admin Commands*\n"
            "/admin stats\n"
            "/admin event <type>\n"
            "/admin multiplier <amount> <hours>\n"
            "/admin exile @user <hours>\n"
            "/admin spawn boss\n"
            "/admin reset_factions\n"
            "/admin give @user <item> <rarity>",
            parse_mode="Markdown"
        )
        return

    subcmd = context.args[0].lower()

    # ── stats ──────────────────────────────────────────────────────────────
    if subcmd == "stats":
        stats = get_ecosystem_stats()
        top = stats["top_user"]
        
        # Guard against key formatting variations in user structures
        username_text = "No users yet."
        if top:
            username = top.get('username') or f"Croco#{top.get('user_id', '?')}"
            username_text = f"👑 Top Croco: @{username} ({top['xp']:,} XP)"
            
        await update.message.reply_text(
            f"📊 *Ecosystem Stats*\n"
            f"━━━━━━━━━━━━\n"
            f"👥 Total Crocos: {stats['total_users']}\n"
            f"🔥 Active Today: {stats['active_today']}\n"
            f"{username_text}",
            parse_mode="Markdown"
        )

    # ── event ──────────────────────────────────────────────────────────────
    elif subcmd == "event":
        if len(context.args) < 2:
            await update.message.reply_text(f"Types: {', '.join(WORLD_EVENTS.keys())}")
            return
        event_type = context.args[1]
        if event_type not in WORLD_EVENTS:
            await update.message.reply_text("Unknown event.")
            return
        ev = WORLD_EVENTS[event_type]
        start_world_event(event_type, ev["duration_hours"])
        await send_sticker(context.bot, GROUP_ID, ev.get("sticker", "shocked"))
        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=(
                f"⚡ *ADMIN TRIGGERED EVENT*\n"
                f"{ev['name']}\n_{ev['desc']}_\n"
                f"XP ×{ev['xp_multiplier']} for {ev['duration_hours']}h"
            ),
            parse_mode="Markdown"
        )

    # ── exile ──────────────────────────────────────────────────────────────
    elif subcmd == "exile":
        if len(context.args) < 3:
            await update.message.reply_text("Usage: /admin exile @username <hours>")
            return
        target_username = context.args[1].lstrip("@")
        try:
            hours = int(context.args[2])
        except ValueError:
            await update.message.reply_text("Hours must be a number.")
            return

        conn = get_conn()
        row = conn.execute("SELECT user_id FROM users WHERE username=?", (target_username,)).fetchone()
        conn.close()
        if not row:
            await update.message.reply_text("User not found.")
            return

        exile_until = datetime.now().timestamp() + hours * 3600
        update_user(row["user_id"], exile_until=exile_until)
        await send_sticker(context.bot, GROUP_ID, "angry_god")
        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=f"🔴 *@{target_username}* has been exiled for *{hours} hour(s)* by the swamp admins.",
            parse_mode="Markdown"
        )

    # ── spawn boss ─────────────────────────────────────────────────────────
    elif subcmd == "spawn" and len(context.args) > 1 and context.args[1] == "boss":
        await send_sticker(context.bot, GROUP_ID, "angry_god")
        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=(
                "💀 *THE ANCIENT ONE AWAKENS*\n"
                "━━━━━━━━━━━━━\n"
                "A legendary boss croco has surfaced from the deep.\n\n"
                "Type /hunt in the next *30 minutes* for a chance at legendary loot.\n"
                "_First 3 successful hunts get bonus drops._"
            ),
            parse_mode="Markdown"
        )

    # ── reset_factions ─────────────────────────────────────────────────────
    elif subcmd == "reset_factions":
        from db.database import get_faction_leaderboard
        rows = get_faction_leaderboard()
        winner = rows[0] if rows else None
        reset_faction_xp()
        msg = "🏆 *TERRITORY WAR ENDED*\n"
        if winner:
            msg += f"👑 Winner: *{winner['faction_name']}* — {winner['total_xp']:,} XP\n"
        msg += "\n_Weekly scores reset. New war begins now._"
        await send_sticker(context.bot, GROUP_ID, "premium_thumbs")
        await context.bot.send_message(chat_id=GROUP_ID, text=msg, parse_mode="Markdown")

    # ── give item ──────────────────────────────────────────────────────────
    elif subcmd == "give":
        if len(context.args) < 4:
            await update.message.reply_text("Usage: /admin give @user <item_name> <rarity>")
            return
        target_username = context.args[1].lstrip("@")
        item_name = context.args[2]
        rarity = context.args[3].capitalize()

        conn = get_conn()
        row = conn.execute("SELECT user_id FROM users WHERE username=?", (target_username,)).fetchone()
        conn.close()
        if not row:
            await update.message.reply_text("User not found.")
            return
        from db.database import add_item
        add_item(row["user_id"], item_name, rarity)
        await update.message.reply_text(f"✅ Gave {rarity} *{item_name}* to @{target_username}.", parse_mode="Markdown")

    else:
        await update.message.reply_text("Unknown admin subcommand.")
