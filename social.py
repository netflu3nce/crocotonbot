import random
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from config import (
    GROUP_ID, AMBUSH_COOLDOWN, PROTECT_COOLDOWN,
    PROTECT_DURATION, REVENGE_WINDOW, GIFT_COOLDOWN,
    FACTIONS,
)
from db.database import (
    ensure_user, get_user, update_user,
    get_cooldown, set_cooldown,
    log_social, add_revenge, get_revenge_target, use_revenge,
    get_inventory, remove_item, add_item, join_faction,
)
from systems.xp import award_xp
from systems.stickers import send_sticker

def get_mentioned_user(context, message):
    """Extract mentioned user from message entities."""
    if not message.entities:
        return None, None
    for entity in message.entities:
        if entity.type == "mention":
            username = message.text[entity.offset + 1: entity.offset + entity.length]
            return username, None
        elif entity.type == "text_mention":
            u = entity.user
            return u.username or u.first_name, u.id
    return None, None

async def get_target_from_db(username):
    from db.database import get_conn
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    conn.close()
    return row

# ── /ambush ────────────────────────────────────────────────────────────────────
async def ambush(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return

    attacker = update.effective_user
    ensure_user(attacker.id, attacker.username or attacker.first_name)
    now = datetime.now().timestamp()

    cd = get_cooldown(attacker.id, "ambush")
    if cd and now < cd:
        remaining = int(cd - now)
        h, m = remaining // 3600, (remaining % 3600) // 60
        await update.message.reply_text(f"⏳ Ambush cooldown: *{h}h {m}m*", parse_mode="Markdown")
        return

    if not context.args:
        await update.message.reply_text("Usage: /ambush @username")
        return

    target_username = context.args[0].lstrip("@")
    target_db = await get_target_from_db(target_username)

    if not target_db:
        await update.message.reply_text("That croco hasn't entered the swamp yet.")
        return

    if target_db["user_id"] == attacker.id:
        await update.message.reply_text("You can't ambush yourself.")
        return

    # Check target protection
    if target_db["protected_until"] and now < target_db["protected_until"]:
        await send_sticker(context.bot, GROUP_ID, "mask_hoodie")
        await update.message.reply_text(
            f"🛡️ @{target_username} is *protected*. Your ambush dissolved into the reeds.",
            parse_mode="Markdown"
        )
        return

    # Success rate based on XP difference
    attacker_db = get_user(attacker.id)
    xp_diff = attacker_db["xp"] - target_db["xp"]
    base_chance = 0.55
    if xp_diff > 1000:
        success_chance = min(0.80, base_chance + 0.15)
    elif xp_diff < -1000:
        success_chance = max(0.25, base_chance - 0.20)
    else:
        success_chance = base_chance

    success = random.random() < success_chance
    set_cooldown(attacker.id, "ambush", AMBUSH_COOLDOWN)

    if success:
        # Steal an item if they have one
        items = get_inventory(target_db["user_id"])
        stolen = None
        if items and random.random() < 0.6:
            item = random.choice(items)
            stolen = item["item_name"]
            rarity = item["rarity"]
            remove_item(target_db["user_id"], stolen)
            add_item(attacker.id, stolen, rarity)

        xp_stolen = random.randint(20, 60)
        from db.database import get_conn
        conn = get_conn()
        conn.execute("UPDATE users SET xp=MAX(0,xp-?) WHERE user_id=?",
                     (xp_stolen, target_db["user_id"]))
        conn.commit()
        conn.close()
        award_xp(attacker.id, 80)

        add_revenge(target_db["user_id"], attacker.id)
        log_social(attacker.id, target_db["user_id"], "ambush", "success")

        msg = (
            f"⚔️ *@{attacker.username}* ambushed *@{target_username}* from the shadows!\n\n"
            f"💀 Stole *{xp_stolen} XP*"
            + (f"\n🎒 Also took: *{stolen}*" if stolen else "")
            + f"\n\n_@{target_username} now has a 24h revenge window._"
        )
        await send_sticker(context.bot, GROUP_ID, "devil_laugh")
    else:
        log_social(attacker.id, target_db["user_id"], "ambush", "failed")
        msg = (
            f"💨 *@{attacker.username}* tried to ambush *@{target_username}*...\n"
            f"and completely missed. Embarrassing."
        )
        await send_sticker(context.bot, GROUP_ID, "laughing")

    await update.message.reply_text(msg, parse_mode="Markdown")

# ── /protect ──────────────────────────────────────────────────────────────────
async def protect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return

    user = update.effective_user
    ensure_user(user.id, user.username or user.first_name)
    now = datetime.now().timestamp()

    cd = get_cooldown(user.id, "protect")
    if cd and now < cd:
        remaining = int(cd - now)
        h, m = remaining // 3600, (remaining % 3600) // 60
        await update.message.reply_text(f"⏳ Protect cooldown: *{h}h {m}m*", parse_mode="Markdown")
        return

    protect_until = now + PROTECT_DURATION
    update_user(user.id, protected_until=protect_until)
    set_cooldown(user.id, "protect", PROTECT_COOLDOWN)

    await send_sticker(context.bot, GROUP_ID, "mask_hoodie")
    await update.message.reply_text(
        f"🛡️ *@{user.username}* enters the shadows.\n"
        f"Protected for *5 hours*. No ambush can reach you.",
        parse_mode="Markdown"
    )

# ── /revenge ──────────────────────────────────────────────────────────────────
async def revenge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return

    user = update.effective_user
    ensure_user(user.id, user.username or user.first_name)
    now = datetime.now().timestamp()

    target_revenge = get_revenge_target(user.id)
    if not target_revenge:
        await update.message.reply_text("No revenge available. No one has wronged you... yet.")
        return

    from db.database import get_conn
    conn = get_conn()
    attacker_row = conn.execute(
        "SELECT username FROM users WHERE user_id=?",
        (target_revenge["attacker_id"],)
    ).fetchone()
    conn.close()

    attacker_name = attacker_row["username"] if attacker_row else "Unknown"

    # Higher success rate for revenge
    success = random.random() < 0.70
    use_revenge(target_revenge["id"])

    if success:
        xp_taken = random.randint(30, 80)
        conn = get_conn()
        conn.execute("UPDATE users SET xp=MAX(0,xp-?) WHERE user_id=?",
                     (xp_taken, target_revenge["attacker_id"]))
        conn.commit()
        conn.close()
        award_xp(user.id, 60)
        log_social(user.id, target_revenge["attacker_id"], "revenge", "success")

        await send_sticker(context.bot, GROUP_ID, "angry_god")
        await update.message.reply_text(
            f"🔥 *@{user.username}* took revenge on *@{attacker_name}*!\n"
            f"⚡ Recovered + stole *{xp_taken} XP*. Justice served in the swamp.",
            parse_mode="Markdown"
        )
    else:
        log_social(user.id, target_revenge["attacker_id"], "revenge", "failed")
        await send_sticker(context.bot, GROUP_ID, "weary")
        await update.message.reply_text(
            f"💀 *@{user.username}* tried to avenge themselves against *@{attacker_name}*...\n"
            f"and failed. The swamp is merciless.",
            parse_mode="Markdown"
        )

# ── /gift ─────────────────────────────────────────────────────────────────────
async def gift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return

    user = update.effective_user
    ensure_user(user.id, user.username or user.first_name)
    now = datetime.now().timestamp()

    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Usage: /gift @username ItemName")
        return

    target_username = context.args[0].lstrip("@")
    item_name = " ".join(context.args[1:])

    cd = get_cooldown(user.id, "gift")
    if cd and now < cd:
        await update.message.reply_text("⏳ You can only gift once per day.")
        return

    # Check user has item
    items = get_inventory(user.id)
    found = None
    for item in items:
        if item["item_name"].lower() == item_name.lower():
            found = item
            break

    if not found:
        await update.message.reply_text(f"You don't have *{item_name}* in your inventory.", parse_mode="Markdown")
        return

    target = await get_target_from_db(target_username)
    if not target:
        await update.message.reply_text("That croco doesn't exist in the swamp.")
        return

    remove_item(user.id, found["item_name"])
    add_item(target["user_id"], found["item_name"], found["rarity"])
    set_cooldown(user.id, "gift", GIFT_COOLDOWN)
    award_xp(user.id, 15)

    await send_sticker(context.bot, GROUP_ID, "bro_hug")
    await update.message.reply_text(
        f"🎁 *@{user.username}* gifted *{found['item_name']}* to *@{target_username}*.\n"
        f"_Reputation +1. The swamp remembers kindness._",
        parse_mode="Markdown"
    )
    conn = get_conn()
    conn.execute("UPDATE users SET reputation=reputation+1 WHERE user_id=?", (user.id,))
    conn.commit()
    conn.close()
    from db.database import get_conn

# ── /join ─────────────────────────────────────────────────────────────────────
async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return

    user = update.effective_user
    ensure_user(user.id, user.username or user.first_name)

    if not context.args:
        faction_list = "\n".join(f"• {f}" for f in FACTIONS)
        await update.message.reply_text(
            f"🌿 Choose your territory:\n\n{faction_list}\n\nUsage: /join <faction name>",
        )
        return

    faction_input = " ".join(context.args).title()
    matched = next((f for f in FACTIONS if f.lower() == faction_input.lower()), None)

    if not matched:
        await update.message.reply_text(
            f"Unknown faction. Choose from:\n" + "\n".join(f"• {f}" for f in FACTIONS)
        )
        return

    db_user = get_user(user.id)
    if db_user["faction"] == matched:
        await update.message.reply_text(f"You're already in *{matched}*.", parse_mode="Markdown")
        return

    join_faction(user.id, matched)
    await send_sticker(context.bot, GROUP_ID, "hi")
    await update.message.reply_text(
        f"🌿 *@{user.username}* has entered *{matched}*.\n"
        f"Hunt, raid, and defend your territory. Glory awaits.",
        parse_mode="Markdown"
    )
