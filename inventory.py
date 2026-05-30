import random
from config import ITEM_POOL
from db.database import add_item, get_inventory

RARITY_EMOJI = {
    "Common":    "⬜",
    "Uncommon":  "🟩",
    "Rare":      "🟦",
    "Epic":      "🟪",
    "Legendary": "🟨",
}

def roll_item():
    """Weighted random item drop. Returns (name, rarity) or None."""
    total = sum(w for _, _, w in ITEM_POOL)
    r = random.uniform(0, total)
    cumulative = 0
    for name, rarity, weight in ITEM_POOL:
        cumulative += weight
        if r <= cumulative:
            return name, rarity
    return ITEM_POOL[0][0], ITEM_POOL[0][1]

def give_item(user_id, item_name=None, rarity=None):
    """Give a specific or random item to user."""
    if item_name is None:
        item_name, rarity = roll_item()
    add_item(user_id, item_name, rarity)
    return item_name, rarity

def format_inventory(user_id) -> str:
    items = get_inventory(user_id)
    if not items:
        return "🎒 Your inventory is empty. Start hunting."

    lines = ["🎒 *Inventory*\n"]
    for item in items:
        emoji = RARITY_EMOJI.get(item["rarity"], "⬜")
        lines.append(f"{emoji} {item['item_name']} ×{item['quantity']} _{item['rarity']}_")
    return "\n".join(lines)
