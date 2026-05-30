import random
from config import COMPANION_POOL, EGG_HATCH_PROGRESS
from db.database import (
    add_egg, get_active_egg, update_egg_progress,
    hatch_egg, add_companion
)

def try_drop_egg(user_id) -> bool:
    """3% chance to find an egg on hunt. Only if no active egg."""
    existing = get_active_egg(user_id)
    if existing:
        return False
    if random.random() < 0.03:
        add_egg(user_id)
        return True
    return False

def progress_egg(user_id, amount: int) -> dict:
    """Add progress to active egg, hatch if ready."""
    egg = get_active_egg(user_id)
    if not egg:
        return {"has_egg": False}

    new_progress = egg["progress"] + amount
    update_egg_progress(egg["egg_id"], amount)

    if new_progress >= EGG_HATCH_PROGRESS:
        return do_hatch(user_id, egg["egg_id"])

    return {
        "has_egg": True,
        "hatched": False,
        "progress": new_progress,
        "max": EGG_HATCH_PROGRESS,
    }

def do_hatch(user_id, egg_id) -> dict:
    """Perform the hatch and assign companion."""
    hatch_egg(egg_id)
    companion_name, variant = roll_companion()
    add_companion(user_id, companion_name, variant)
    return {
        "has_egg": True,
        "hatched": True,
        "companion_name": companion_name,
        "variant": variant,
    }

def roll_companion():
    total = sum(w for _, _, w in COMPANION_POOL)
    r = random.uniform(0, total)
    cumulative = 0
    for name, variant, weight in COMPANION_POOL:
        cumulative += weight
        if r <= cumulative:
            return name, variant
    return COMPANION_POOL[0][0], COMPANION_POOL[0][1]

COMPANION_EMOJI = {
    "Common":    "🐊",
    "Uncommon":  "🌿",
    "Rare":      "⚡",
    "Epic":      "💜",
    "Legendary": "👑",
    "Corrupted": "🌑",
}
