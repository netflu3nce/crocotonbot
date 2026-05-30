from config import RANKS
from db.database import get_user, update_user, add_xp as db_add_xp, add_faction_xp

def get_rank_for_xp(xp: int) -> str:
    current_rank = RANKS[0][1]
    for threshold, rank_name in RANKS:
        if xp >= threshold:
            current_rank = rank_name
    return current_rank

def get_next_rank(xp: int):
    for i, (threshold, rank_name) in enumerate(RANKS):
        if xp < threshold:
            return rank_name, threshold
    return None, None  # already max rank

def award_xp(user_id, amount: int, event_multiplier: float = 1.0) -> dict:
    """Award XP, check for rank up, return result dict."""
    user = get_user(user_id)
    if not user:
        return {}

    # Hunger penalty
    hunger_mult = 1.0
    if user["hunger"] >= 5:
        hunger_mult = 0.5
    elif user["hunger"] >= 3:
        hunger_mult = 0.75

    final_amount = int(amount * event_multiplier * hunger_mult)
    old_xp = user["xp"]
    new_xp = old_xp + final_amount

    old_rank = get_rank_for_xp(old_xp)
    new_rank = get_rank_for_xp(new_xp)

    db_add_xp(user_id, final_amount)
    update_user(user_id, rank=new_rank)

    # Faction XP contribution
    if user["faction"]:
        add_faction_xp(user["faction"], final_amount)

    ranked_up = old_rank != new_rank
    return {
        "xp_gained": final_amount,
        "new_xp": new_xp,
        "old_rank": old_rank,
        "new_rank": new_rank,
        "ranked_up": ranked_up,
        "hunger_penalty": hunger_mult < 1.0,
    }

def rank_index(rank_name: str) -> int:
    for i, (_, r) in enumerate(RANKS):
        if r == rank_name:
            return i
    return 0

def is_predator_or_above(user) -> bool:
    return rank_index(user["rank"]) >= 4  # Predator is index 4

def xp_progress_bar(xp: int) -> str:
    """Visual XP bar for profile."""
    for i, (threshold, rank_name) in enumerate(RANKS):
        if i + 1 < len(RANKS):
            next_threshold = RANKS[i + 1][0]
            if xp < next_threshold:
                prev = threshold
                progress = xp - prev
                total = next_threshold - prev
                filled = int((progress / total) * 10)
                bar = "█" * filled + "░" * (10 - filled)
                pct = int((progress / total) * 100)
                return f"[{bar}] {pct}%"
    return "[██████████] MAX"
