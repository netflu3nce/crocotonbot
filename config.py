import os

# ── Bot Core ──────────────────────────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://your-render-url.onrender.com")
PORT = int(os.getenv("PORT", 8080))

# ── Community ─────────────────────────────────────────────────────────────────
GROUP_ID = -1003833863769
GROUP_LINK = "https://t.me/Crocotoncommunity"
CA_ADDRESS = "EQB-i1kqPz_MitkRCOzzgDf0_doxahk1bUPVAGjm49zMozOd"
START_IMAGE = "https://i.ibb.co/35V7TDLW/IMG-9243.jpg"

# ── Admin IDs (add your Telegram user ID here) ────────────────────────────────
ADMIN_IDS = [7608551523 , 544346155]  # Majek's ID & Founder's ID — add more as needed

# ── Cooldowns (seconds) ───────────────────────────────────────────────────────
HUNT_COOLDOWN = 8 * 3600       # 8 hours
AMBUSH_COOLDOWN = 12 * 3600    # 12 hours
PROTECT_COOLDOWN = 24 * 3600   # 24 hours
PROTECT_DURATION = 5 * 3600    # 5 hours
REVENGE_WINDOW = 24 * 3600     # 24 hours
GIFT_COOLDOWN = 24 * 3600      # 24 hours

# ── XP Values ─────────────────────────────────────────────────────────────────
XP_HUNT_SUCCESS = 50
XP_HUNT_RARE = 120
XP_HUNT_JACKPOT = 300
XP_HUNT_FAIL = 10
XP_AMBUSH_WIN = 80
XP_AMBUSH_LOSS = 20
XP_EVENT_PARTICIPATE = 60
XP_STREAK_BONUS = 25       # per streak day after day 3

# ── Rank Thresholds ───────────────────────────────────────────────────────────
RANKS = [
    (0,       "🥚 Tadpole"),
    (200,     "🐊 Hatchling"),
    (600,     "🌿 Swamp Runner"),
    (1500,    "🎯 Hunter"),
    (4000,    "⚔️ Predator"),
    (10000,   "👑 Apex Croco"),
    (25000,   "🦴 Ancient Croco"),
    (60000,   "🌑 Swamp King"),
]

# ── Factions ──────────────────────────────────────────────────────────────────
FACTIONS = ["Black Swamp", "Deep Waters", "Red Marsh", "Fog Hollow"]

# ── Item Drop Pool ────────────────────────────────────────────────────────────
# (name, rarity, weight)
ITEM_POOL = [
    ("Swamp Bone",     "Common",    40),
    ("Murky Scale",    "Common",    35),
    ("River Stone",    "Common",    30),
    ("Venom Sac",      "Uncommon",  20),
    ("Ancient Bone",   "Uncommon",  15),
    ("Black Egg",      "Rare",       8),
    ("Golden Scale",   "Rare",       6),
    ("Crown Fragment", "Epic",       3),
    ("Fossil Relic",   "Epic",       2),
    ("Void Crystal",   "Legendary",  0.5),
]

# ── Egg Hatch Thresholds ──────────────────────────────────────────────────────
EGG_HATCH_PROGRESS = 100
EGG_HUNT_BONUS = 5
EGG_EVENT_BONUS = 15
EGG_STREAK_BONUS = 3

# ── Companion Types ───────────────────────────────────────────────────────────
COMPANION_POOL = [
    ("Common Croco",     "Common",    50),
    ("Swamp Stalker",    "Uncommon",  25),
    ("Mutant Croco",     "Rare",      15),
    ("Neon Croco",       "Epic",       7),
    ("Legendary Apex",   "Legendary",  2.5),
    ("Corrupted One",    "Corrupted",  0.5),
]

# ── Sticker File IDs ──────────────────────────────────────────────────────────
STICKERS = {
    "laughing":        "CAACAgIAAxkBAAFLAAFjaholf26M8yAq7CE5uHx39pSjZkUAAjIJAAIYQu4IEfuMde-Y59o7BA",
    "heart":           "CAACAgIAAxkBAAFLAAFmaholn7VpIudoX73Hig6iCA4mr4kAAhgJAAIYQu4IB4Htqc_2Mms7BA",
    "thumbs_up":       "CAACAgIAAxkBAAFLAAFraholvSA3ffI1VD9YqL621LZJhwgAAhsJAAIYQu4I3Lml1fNKrsg7BA",
    "shocked":         "CAACAgIAAxkBAAFLAAFtahol2HEMJOx_ahoHIyp_g7g4nRoAAhkJAAIYQu4I5wNxMAVB2O87BA",
    "hi":              "CAACAgIAAxkBAAFLAAFvahol7ie2vpvRfckUAtHgVQZVBTQAAh4JAAIYQu4I-VjZ7h0hnCE7BA",
    "catching_love":   "CAACAgIAAxkBAAFLAAFxahomBMAZWJXHHs6Wn8f7KXprfuUAAhUJAAIYQu4IezjxVtITLgY7BA",
    "hungry":          "CAACAgIAAxkBAAFLAAF0ahomIRBD_je1vscOwOeHln8CbzcAAhYJAAIYQu4IpsVwf8FjDq07BA",
    "in_love":         "CAACAgIAAxkBAAFLAAF7ahomVHzmO22Sq6ch9xp_kX4Xn8YAAhcJAAIYQu4IhFp6oBw3mtY7BA",
    "rainbow":         "CAACAgIAAxkBAAFLAAF9ahombZHWe2B5YVNBlsr7q47XSX0AAhQJAAIYQu4Iifzp3KsnLpQ7BA",
    "bro_hug":         "CAACAgIAAxkBAAFLAAF_ahomo58FgxJY-kBvUQ23rTFKHpQAAhoJAAIYQu4IyF8y3k_hoZE7BA",
    "mask_hoodie":     "CAACAgIAAxkBAAFLAAGBahomybUJEh3M1IWlilNTYNGejRYAAhwJAAIYQu4IhdT3h_EY0ao7BA",
    "full_stomach":    "CAACAgIAAxkBAAFLAAGFahom-Fa_J18HPFaQEoMrc6RJWaIAAh0JAAIYQu4Ihkbtyw0BP547BA",
    "nervous":         "CAACAgIAAxkBAAFLAAGIahonG3Y7qeJ4f7LlfSAHMb9RkdQAAh8JAAIYQu4IF5gGjvs_PGY7BA",
    "typing":          "CAACAgIAAxkBAAFLAAGKahonPTfb3DDojrEsZbCyaoX2Gn0AAiAJAAIYQu4I4YogqKE6Ctk7BA",
    "devil_laugh":     "CAACAgIAAxkBAAFLAAGMahonY_sXPCPCGmnmee_mAUcWYjcAAiEJAAIYQu4ICwqcOU7QWFA7BA",
    "freezing":        "CAACAgIAAxkBAAFLAAGOahongU-CS8i2YiFhJWGtnrF_nlQAAiIJAAIYQu4IsJEOZWcMR6A7BA",
    "sad":             "CAACAgIAAxkBAAFLAAGQahonpMTmusE9wlyVRfH4zzSLdKgAAiMJAAIYQu4Is-ojokoMccc7BA",
    "sleeping":        "CAACAgIAAxkBAAFLAAGUahont5-CaIY1OM1_av1RmrJ7GeYAAiQJAAIYQu4IcFQQ1PhauRY7BA",
    "crying":          "CAACAgIAAxkBAAFLAAGZahon2DMfhIavhJh_pePgF0Kza44AAiUJAAIYQu4IYfZZ3ibaauU7BA",
    "thinking":        "CAACAgIAAxkBAAFLAAGcahon7h7v4-7_dpyNYNzufsS34EQAAiYJAAIYQu4Io6vyRjH4o447BA",
    "happy":           "CAACAgIAAxkBAAFLAAGgahooBvj6XC5MwStMvwV0Fdos_SwAAicJAAIYQu4IEp9SzHgd2v07BA",
    "weary":           "CAACAgIAAxkBAAFLAAGiahooKJpmoHZdEN-2uZzsfLqF0PgAAigJAAIYQu4IWeEphabQ-bk7BA",
    "excuse_me":       "CAACAgIAAxkBAAFLAAGqahooSjwAAe8ocAnw6u4OniPu06HmAAIpCQACGELuCI30vyqLmbodOwQ",
    "consoling":       "CAACAgIAAxkBAAFLAAGuahoodLuIoq5EIywBLhkq9kT82VEAAioJAAIYQu4Is489Kshp5RE7BA",
    "shrug":           "CAACAgIAAxkBAAFLAAGwahoopS-JhIb4otbtXxfBsPcZMx0AAiwJAAIYQu4I3Nn2OYvLeM07BA",
    "cool_wink":       "CAACAgIAAxkBAAFLAAGyahooyxTNBn3uq3S3i78bCu8ZMAMAAi4JAAIYQu4IZseiMK-8sfQ7BA",
    "nauseated":       "CAACAgIAAxkBAAFLAAG0ahoo8LK_o6-J9x1eoYK8CmNVjrQAAjMJAAIYQu4I7Px-kXpp_Kk7BA",
    "please":          "CAACAgIAAxkBAAFLAAG2ahopCpkh1dLP-DcKMWbM9sJwboQAAjcJAAIYQu4I16TspS-5FxA7BA",
    "hyper_coffee":    "CAACAgIAAxkBAAFLAAG7ahopLscZLSPfJ4aRe2ZKPRK7oeoAAjUJAAIYQu4IMdeOPA02qbw7BA",
    "angry_god":       "CAACAgIAAxkBAAFLAAHEahopbYApK2s-gEeY1mzpWeO2GpUAAjYJAAIYQu4I6eoDOYsvpFI7BA",
    "premium_thumbs":  "CAACAgIAAxkBAAFLAAHKahop4cLftctV5Hn7hEymbleMBocAAkEZAALs-ylIoifqfySX4Ew7BA",
    "premium_flex":    "CAACAgIAAxkBAAFLAAHOahoqDaAiIL6b8bADV2zOg9BccBwAAgoeAAIkFMFJvDGzJJGdXnk7BA",
    "premium_love":    "CAACAgIAAxkBAAFLAAHQahoqLuDVS7veJ_dI3VXf5UuDoNkAAq0XAAJLIslJD8KUx9_NKeY7BA",
}

# ── World Event Types ─────────────────────────────────────────────────────────
WORLD_EVENTS = {
    "blood_moon": {
        "name": "🔴 Blood Moon",
        "desc": "The swamp bleeds red. Rare predators emerge. Danger multiplied.",
        "xp_multiplier": 2.0,
        "duration_hours": 3,
        "sticker": "angry_god",
    },
    "drought": {
        "name": "☀️ The Drought",
        "desc": "Waters recede. Resources vanish. Only the strongest survive.",
        "xp_multiplier": 0.6,
        "duration_hours": 4,
        "sticker": "sad",
    },
    "mutation_storm": {
        "name": "⚡ Mutation Storm",
        "desc": "Lightning fractures the swamp. Transformations are unpredictable.",
        "xp_multiplier": 1.5,
        "duration_hours": 2,
        "sticker": "shocked",
    },
    "swamp_flood": {
        "name": "🌊 Swamp Flood",
        "desc": "Territories shift. Loot redistributes. Nothing is permanent.",
        "xp_multiplier": 1.3,
        "duration_hours": 3,
        "sticker": "freezing",
    },
    "feeding_frenzy": {
        "name": "🍖 Feeding Frenzy",
        "desc": "Prey everywhere. Hunt rates surge. Feed or be forgotten.",
        "xp_multiplier": 1.8,
        "duration_hours": 2,
        "sticker": "hungry",
    },
}

# ── Hunt Outcome Weights ──────────────────────────────────────────────────────
HUNT_OUTCOMES = {
    "success":      50,
    "rare_prey":    15,
    "jackpot":       5,
    "fail":         20,
    "ambushed":      5,
    "mutation":      3,
    "hidden_item":   2,
}

# ── Corruption Thresholds ─────────────────────────────────────────────────────
CORRUPTION_GAIN_PER_HUNT = 0.5   # % per hunt above Predator rank
CORRUPTION_COLLAPSE_THRESHOLD = 80
CORRUPTION_COLLAPSE_CHANCE = 0.10  # 10% chance per hunt above 80%
o
