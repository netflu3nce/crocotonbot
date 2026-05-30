import random
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from config import GROUP_ID
from db.database import ensure_user, get_user, get_companion, get_active_egg
from systems.xp import xp_progress_bar, get_next_rank
from systems.corruption import corruption_bar
from systems.inventory import format_inventory
from systems.hunger import get_hunger_message
from systems.stickers import send_sticker
from systems.eggs import COMPANION_EMOJI

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        await update.message.reply_text("🐊 Use this in the Croco community group!")
        return

    user = update.effective_user
    ensure_user(user.id, user.username or user.first_name)

    # Target self or mentioned user
    target_id = user.id
    target_name = user.username or user.first_name
    if context.args:
        await update.message.reply_text("🐊 Tag feature coming soon. Showing your profile.")

    db_user = get_user(target_id)
    if not db_user:
        await update.message.reply_text("No croco found. Type /hunt to begin.")
        return

    companion = get_companion(target_id)
    egg = get_active_egg(target_id)
    now = datetime.now().timestamp()

    hunger_msg = get_hunger_message(db_user["hunger"])
    progress = xp_progress_bar(db_user["xp"])
    next_rank_name, next_threshold = get_next_rank(db_user["xp"])

    streak = db_user["hunt_streak"]
    faction = db_user["faction"] or "None"
    corruption = db_user["corruption"]

    lines = [
        f"🐊 *@{target_name}*",
        f"━━━━━━━━━━━━━━━",
        f"🏅 *Rank:* {db_user['rank']}",
        f"⚡ *XP:* {db_user['xp']:,}",
        f"📈 *Progress:* {progress}",
    ]

    if next_rank_name:
        needed = next_threshold - db_user["xp"]
        lines.append(f"🎯 *Next:* {next_rank_name} _(need {needed:,} XP)_")

    lines += [
        f"🔥 *Hunt Streak:* {streak} day{'s' if streak != 1 else ''}",
        f"🍖 *Hunger:* {db_user['hunger']}/10",
        f"🌿 *Faction:* {faction}",
        f"⭐ *Reputation:* {db_user['reputation']}",
    ]

    if corruption > 0:
        lines.append(f"🌑 *Corruption:* {corruption_bar(corruption)}")

    if companion:
        emoji = COMPANION_EMOJI.get(companion["variant"], "🐊")
        lines.append(f"\n{emoji} *Companion:* {companion['name']} _{companion['variant']}_ Lv.{companion['level']}")

    if egg:
        lines.append(f"🥚 *Active Egg:* {egg['progress']}/100 progress")

    if hunger_msg:
        lines.append(f"\n_{hunger_msg}_")

    # Protected?
    if db_user["protected_until"] and now < db_user["protected_until"]:
        remaining = int((db_user["protected_until"] - now) / 60)
        lines.append(f"\n🛡️ *Protected* for {remaining} more minutes")

    await send_sticker(context.bot, GROUP_ID, "in_love")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def inventory_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return
    user = update.effective_user
    ensure_user(user.id, user.username or user.first_name)
    text = format_inventory(user.id)
    await update.message.reply_text(text, parse_mode="Markdown")


async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return
    from db.database import get_leaderboard
    rows = get_leaderboard(10)
    if not rows:
        await update.message.reply_text("No croco has hunted yet. Be the first.")
        return

    medals = ["🥇", "🥈", "🥉"] + ["🔹"] * 7
    lines = ["👑 *SWAMP LEADERBOARD*", "━━━━━━━━━━━━━"]
    for i, row in enumerate(rows):
        name = row["username"] or f"Croco#{row['user_id']}"
        faction = f" [{row['faction']}]" if row["faction"] else ""
        lines.append(f"{medals[i]} @{name}{faction} — *{row['xp']:,} XP* _{row['rank']}_")

    await send_sticker(context.bot, GROUP_ID, "premium_thumbs")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def factions_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return
    from db.database import get_faction_leaderboard
    rows = get_faction_leaderboard()
    lines = ["🌿 *TERRITORY WAR — FACTION STANDINGS*", "━━━━━━━━━━━━━"]
    medals = ["🥇", "🥈", "🥉", "🔸"]
    for i, row in enumerate(rows):
        m = medals[i] if i < 4 else "🔸"
        lines.append(
            f"{m} *{row['faction_name']}* — {row['total_xp']:,} XP | {row['member_count']} members"
        )
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
