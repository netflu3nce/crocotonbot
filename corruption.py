import random
from config import (
    CORRUPTION_GAIN_PER_HUNT,
    CORRUPTION_COLLAPSE_THRESHOLD,
    CORRUPTION_COLLAPSE_CHANCE,
)
from db.database import get_user, update_user, get_inventory, remove_item
from systems.xp import is_predator_or_above

def tick_corruption(user_id) -> float:
    """Add corruption per hunt for high-rank users."""
    user = get_user(user_id)
    if not user or not is_predator_or_above(user):
        return user["corruption"] if user else 0

    new_corruption = min(user["corruption"] + CORRUPTION_GAIN_PER_HUNT, 100)
    update_user(user_id, corruption=new_corruption)
    return new_corruption

def check_collapse(user_id) -> dict:
    """Check if user collapses from corruption. Returns result dict."""
    user = get_user(user_id)
    if not user:
        return {"collapsed": False}

    corruption = user["corruption"]
    if corruption < CORRUPTION_COLLAPSE_THRESHOLD:
        return {"collapsed": False, "corruption": corruption}

    if random.random() < CORRUPTION_COLLAPSE_CHANCE:
        return trigger_collapse(user_id, user)

    return {"collapsed": False, "corruption": corruption, "danger": True}

def trigger_collapse(user_id, user) -> dict:
    """Execute corruption collapse."""
    from datetime import datetime
    # Lose 30% XP
    xp_loss = int(user["xp"] * 0.3)
    new_xp = max(0, user["xp"] - xp_loss)

    # Lose a random item
    items = get_inventory(user_id)
    lost_item = None
    if items:
        item = random.choice(items)
        lost_item = item["item_name"]
        remove_item(user_id, lost_item)

    # Exile for 2 hours
    exile_until = datetime.now().timestamp() + 7200
    update_user(user_id,
                xp=new_xp,
                corruption=0,
                exile_until=exile_until,
                hunt_streak=0)

    return {
        "collapsed": True,
        "xp_loss": xp_loss,
        "lost_item": lost_item,
        "exile_hours": 2,
    }

def corruption_bar(corruption: float) -> str:
    filled = int(corruption / 10)
    bar = "▓" * filled + "░" * (10 - filled)
    return f"[{bar}] {corruption:.1f}%"
