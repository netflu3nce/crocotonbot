import random
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from config import (
    GROUP_ID, HUNT_COOLDOWN, HUNT_OUTCOMES,
    XP_HUNT_SUCCESS, XP_HUNT_RARE, XP_HUNT_JACKPOT, XP_HUNT_FAIL,
    XP_STREAK_BONUS, EGG_HUNT_BONUS,
)
from db.database import (
    ensure_user, get_user, update_user,
    get_cooldown, set_cooldown, get_active_event,
)
from systems.xp import award_xp, get_next_rank
from systems.inventory import give_item, RARITY_EMOJI
from systems.eggs import try_drop_egg, progress_egg, COMPANION_EMOJI
from systems.corruption import tick_corruption, check_collapse
from systems.hunger import reset_hunger, get_hunger_message
from systems.stickers import send_sticker

def weighted_choice(outcomes: dict) -> str:
    total = sum(outcomes.values())
    r = random.uniform(0, total)
    cumulative = 0
    for key, weight in outcomes.items():
        cumulative += weight
        if r <= cumulative:
            return key
    return list(outcomes.keys())[0]

SUCCESS_MESSAGES = [
    "🐊 You slipped through the murk and struck. Prey secured.",
    "🎯 Clean kill. The swamp bows.",
    "🌿 You moved like shadow. The hunt was yours before it began.",
    "⚔️ Tooth met flesh. You fed well today.",
]
FAIL_MESSAGES = [
    "💨 Your prey vanished into the reeds. Nothing.",
    "🌀 The swamp gave nothing today. Try again.",
    "😤 Missed. The swamp keeps its secrets.",
    "😔 Prey escaped. Hunger persists.",
]
RARE_MESSAGES = [
    "✨ A rare creature crossed your path. You moved FAST.",
    "🦎 Uncommon prey. Taken with precision.",
    "💎 Something unusual. Something valuable.",
]
JACKPOT_MESSAGES = [
    "🏆 LEGENDARY PREY. The whole swamp felt this hunt.",
    "👑 You just hit the swamp jackpot. APEX behavior.",
    "🌟 Once in a season drop. Don't waste it.",
]
AMBUSHED_MESSAGES = [
    "⚠️ Something was waiting for YOU. You walked into a trap.",
    "🩸 Ambushed from the deep. Lost something.",
    "💀 The swamp ambushed the hunter. Humbling.",
]
MUTATION_MESSAGES = [
    "⚡ A surge of energy courses through you. Something changed.",
    "🧬 Mutation detected. Your croco shifts.",
    "🌀 The swamp rewrites your code.",
]

async def hunt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        await update.message.reply_text("🐊 Hunt commands only work in the Croco community group!")
        return

    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name

    ensure_user(user_id, username)
    db_user = get_user(user_id)
    now = datetime.now().timestamp()

    # ── Exile check ────────────────────────────────────────────────────────
    if db_user["exile_until"] and now < db_user["exile_until"]:
        remaining = int((db_user["exile_until"] - now) / 60)
        await send_sticker(context.bot, GROUP_ID, "nervous")
        await update.message.reply_text(
            f"🔴 @{username} you're in *exile*. The swamp rejected you.\n"
            f"Return in *{remaining} minutes.*",
            parse_mode="Markdown"
        )
        return

    # ── Cooldown check ─────────────────────────────────────────────────────
    cooldown_expires = get_cooldown(user_id, "hunt")
    if cooldown_expires and now < cooldown_expires:
        remaining = int(cooldown_expires - now)
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        await send_sticker(context.bot, GROUP_ID, "sleeping")
        await update.message.reply_text(
            f"⏳ @{username} your croco is still recovering.\n"
            f"Next hunt in *{hours}h {minutes}m*.",
            parse_mode="Markdown"
        )
        return

    # ── Active event multiplier ────────────────────────────────────────────
    event = get_active_event()
    from config import WORLD_EVENTS
    xp_multiplier = 1.0
    event_note = ""
    if event:
        ev_config = WORLD_EVENTS.get(event["event_type"], {})
        xp_multiplier = ev_config.get("xp_multiplier", 1.0)
        event_note = f"\n_{ev_config.get('name', '')} is active — XP ×{xp_multiplier}_"

    # ── Determine outcome ──────────────────────────────────────────────────
    outcome = weighted_choice(HUNT_OUTCOMES)

    # Update streak
    last_hunt = db_user["last_hunt"] or 0
    hours_since = (now - last_hunt) / 3600
    streak = db_user["hunt_streak"]

    if hours_since <= 32:  # within streak window
        streak += 1
    else:
        streak = 1

    streak_bonus = max(0, (streak - 2)) * XP_STREAK_BONUS

    # ── Process outcome ────────────────────────────────────────────────────
    if outcome == "success":
        base_xp = XP_HUNT_SUCCESS + streak_bonus
        result = award_xp(user_id, base_xp, xp_multiplier)
        msg_text = random.choice(SUCCESS_MESSAGES)
        await send_sticker(context.bot, GROUP_ID, "thumbs_up")

    elif outcome == "rare_prey":
        base_xp = XP_HUNT_RARE + streak_bonus
        result = award_xp(user_id, base_xp, xp_multiplier)
        item_name, rarity = give_item(user_id)
        msg_text = (
            f"{random.choice(RARE_MESSAGES)}\n\n"
            f"🎁 *Found:* {RARITY_EMOJI.get(rarity, '⬜')} {item_name} _{rarity}_"
        )
        await send_sticker(context.bot, GROUP_ID, "rainbow")

    elif outcome == "jackpot":
        base_xp = XP_HUNT_JACKPOT + streak_bonus
        result = award_xp(user_id, base_xp, xp_multiplier)
        item_name, rarity = give_item(user_id)
        msg_text = (
            f"{random.choice(JACKPOT_MESSAGES)}\n\n"
            f"🏆 *Loot:* {RARITY_EMOJI.get(rarity, '⬜')} {item_name} _{rarity}_"
        )
        await send_sticker(context.bot, GROUP_ID, "premium_flex")

    elif outcome == "fail":
        result = award_xp(user_id, XP_HUNT_FAIL, xp_multiplier)
        msg_text = random.choice(FAIL_MESSAGES)
        await send_sticker(context.bot, GROUP_ID, "sad")

    elif outcome == "ambushed":
        result = award_xp(user_id, 5, 1.0)
        # Lose a random item
        from db.database import get_inventory, remove_item
        items = get_inventory(user_id)
        lost = None
        if items:
            lost_item = random.choice(items)
            lost = lost_item["item_name"]
            remove_item(user_id, lost)
        msg_text = (
            f"{random.choice(AMBUSHED_MESSAGES)}"
            + (f"\n💸 Lost: *{lost}*" if lost else "")
        )
        await send_sticker(context.bot, GROUP_ID, "shocked")

    elif outcome == "mutation":
        base_xp = int(XP_HUNT_SUCCESS * 1.4) + streak_bonus
        result = award_xp(user_id, base_xp, xp_multiplier)
        # Random bonus
        mutation_effect = random.choice([
            "Hunt streak doubled ×2 bonus next hunt.",
            "XP aura activated — nearby allies gain 10 XP.",
            "A faint glow surrounds you. Something shifted.",
        ])
        msg_text = f"{random.choice(MUTATION_MESSAGES)}\n\n✨ _{mutation_effect}_"
        await send_sticker(context.bot, GROUP_ID, "hyper_coffee")

    elif outcome == "hidden_item":
        result = award_xp(user_id, XP_HUNT_SUCCESS, xp_multiplier)
        item_name, rarity = give_item(user_id)
        msg_text = (
            f"🕳️ @{username} discovered something hidden in the swamp...\n\n"
            f"{RARITY_EMOJI.get(rarity, '⬜')} *{item_name}* _{rarity}_ — taken quietly."
        )
        await send_sticker(context.bot, GROUP_ID, "mask_hoodie")
    else:
        result = {"xp_gained": 0, "new_xp": db_user["xp"], "ranked_up": False}
        msg_text = "The swamp was still."

    # ── Update DB ──────────────────────────────────────────────────────────
    update_user(user_id,
                hunt_streak=streak,
                last_hunt=now,
                last_active=now)
    reset_hunger(user_id)
    set_cooldown(user_id, "hunt", HUNT_COOLDOWN)

    # ── Corruption tick (Predator+) ────────────────────────────────────────
    new_corruption = tick_corruption(user_id)
    collapse = check_collapse(user_id)

    # ── Egg progress ───────────────────────────────────────────────────────
    egg_result = progress_egg(user_id, EGG_HUNT_BONUS)
    egg_note = ""
    if egg_result.get("hatched"):
        emoji = COMPANION_EMOJI.get(egg_result["variant"], "🐊")
        egg_note = (
            f"\n\n🥚💥 *EGG HATCHED!*\n"
            f"{emoji} *{egg_result['companion_name']}* _{egg_result['variant']}_ joined you!"
        )
        await send_sticker(context.bot, GROUP_ID, "premium_love")
    elif egg_result.get("has_egg"):
        p = egg_result["progress"]
        m = egg_result["max"]
        egg_note = f"\n🥚 Egg progress: {p}/{m}"

    # ── Try egg drop ───────────────────────────────────────────────────────
    if not egg_result.get("has_egg") and try_drop_egg(user_id):
        egg_note = "\n\n🥚 *You found a mysterious egg in the swamp.* It pulses faintly."
        await send_sticker(context.bot, GROUP_ID, "shocked")

    # ── Streak note ────────────────────────────────────────────────────────
    streak_note = ""
    if streak >= 3:
        streak_note = f"\n🔥 *Streak:* {streak} days — +{streak_bonus} bonus XP"

    # ── Hunger note ───────────────────────────────────────────────────────
    hunger_note = ""
    if result.get("hunger_penalty"):
        hunger_note = f"\n⚠️ _Hunger reduced your XP gains_"

    # ── Rank up ────────────────────────────────────────────────────────────
    rank_note = ""
    if result.get("ranked_up"):
        rank_note = f"\n\n🎉 *RANK UP!*\n{result['old_rank']} → {result['new_rank']}"
        await send_sticker(context.bot, GROUP_ID, "premium_flex")

    # ── Collapse message ───────────────────────────────────────────────────
    collapse_note = ""
    if collapse.get("collapsed"):
        await send_sticker(context.bot, GROUP_ID, "angry_god")
        collapse_note = (
            f"\n\n🌑 *CORRUPTION COLLAPSE*\n"
            f"━━━━━━━━━━\n"
            f"The corruption consumed you.\n"
            f"💀 Lost {collapse['xp_loss']} XP\n"
            + (f"💸 Lost item: *{collapse['lost_item']}*\n" if collapse["lost_item"] else "")
            + f"🔴 Exiled for *2 hours*"
        )

    # ── Final message ──────────────────────────────────────────────────────
    xp_display = result.get("xp_gained", 0)
    new_xp = result.get("new_xp", db_user["xp"])
    final = (
        f"🐊 *@{username}*\n"
        f"━━━━━━━━━━\n"
        f"{msg_text}\n\n"
        f"⚡ *+{xp_display} XP* | Total: *{new_xp:,}*\n"
        f"🏅 *{result.get('new_rank', db_user['rank'])}*"
        + streak_note
        + hunger_note
        + event_note
        + egg_note
        + rank_note
        + collapse_note
    )

    await update.message.reply_text(final, parse_mode="Markdown")
