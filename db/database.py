import sqlite3
import os
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "croco.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        user_id     INTEGER PRIMARY KEY,
        username    TEXT,
        xp          INTEGER DEFAULT 0,
        rank        TEXT DEFAULT '🥚 Tadpole',
        hunger      INTEGER DEFAULT 0,
        reputation  INTEGER DEFAULT 0,
        hunt_streak INTEGER DEFAULT 0,
        last_hunt   REAL DEFAULT 0,
        last_active REAL DEFAULT 0,
        corruption  REAL DEFAULT 0,
        faction     TEXT DEFAULT NULL,
        season_xp   INTEGER DEFAULT 0,
        protected_until REAL DEFAULT 0,
        exile_until REAL DEFAULT 0,
        created_at  REAL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS inventory (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER,
        item_name   TEXT,
        rarity      TEXT,
        quantity    INTEGER DEFAULT 1,
        acquired_at REAL
    );

    CREATE TABLE IF NOT EXISTS eggs (
        egg_id      INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER,
        egg_type    TEXT DEFAULT 'Mystery',
        progress    INTEGER DEFAULT 0,
        hatched     INTEGER DEFAULT 0,
        created_at  REAL
    );

    CREATE TABLE IF NOT EXISTS companions (
        companion_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id      INTEGER,
        name         TEXT,
        variant      TEXT,
        level        INTEGER DEFAULT 1,
        xp           INTEGER DEFAULT 0,
        created_at   REAL
    );

    CREATE TABLE IF NOT EXISTS social_actions (
        action_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        attacker_id INTEGER,
        target_id   INTEGER,
        action_type TEXT,
        result      TEXT,
        timestamp   REAL
    );

    CREATE TABLE IF NOT EXISTS world_events (
        event_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type  TEXT,
        started_at  REAL,
        ends_at     REAL,
        active      INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS factions (
        faction_name  TEXT PRIMARY KEY,
        total_xp      INTEGER DEFAULT 0,
        member_count  INTEGER DEFAULT 0,
        weekly_wins   INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS seasons (
        season_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        start_date   REAL,
        end_date     REAL,
        champion_id  INTEGER,
        champion_name TEXT
    );

    CREATE TABLE IF NOT EXISTS cooldowns (
        user_id     INTEGER,
        action      TEXT,
        expires_at  REAL,
        PRIMARY KEY (user_id, action)
    );

    CREATE TABLE IF NOT EXISTS revenge_queue (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        victim_id   INTEGER,
        attacker_id INTEGER,
        expires_at  REAL,
        used        INTEGER DEFAULT 0
    );
    """)

    # Seed factions
    from config import FACTIONS
    for f in FACTIONS:
        c.execute("INSERT OR IGNORE INTO factions (faction_name) VALUES (?)", (f,))

    conn.commit()
    conn.close()

# ── User Operations ───────────────────────────────────────────────────────────

def get_user(user_id):
    conn = get_conn()
    user = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return user

def ensure_user(user_id, username):
    conn = get_conn()
    conn.execute("""
        INSERT OR IGNORE INTO users (user_id, username, created_at, last_active)
        VALUES (?, ?, ?, ?)
    """, (user_id, username, datetime.now().timestamp(), datetime.now().timestamp()))
    conn.execute("UPDATE users SET username=?, last_active=? WHERE user_id=?",
                 (username, datetime.now().timestamp(), user_id))
    conn.commit()
    conn.close()

def update_user(user_id, **kwargs):
    if not kwargs:
        return
    conn = get_conn()
    sets = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [user_id]
    conn.execute(f"UPDATE users SET {sets} WHERE user_id=?", vals)
    conn.commit()
    conn.close()

def add_xp(user_id, amount):
    conn = get_conn()
    conn.execute("UPDATE users SET xp=xp+?, season_xp=season_xp+? WHERE user_id=?",
                 (amount, amount, user_id))
    conn.commit()
    conn.close()

def get_leaderboard(limit=10):
    conn = get_conn()
    rows = conn.execute(
        "SELECT user_id, username, xp, rank, faction FROM users ORDER BY xp DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return rows

# ── Cooldown Operations ───────────────────────────────────────────────────────

def get_cooldown(user_id, action):
    conn = get_conn()
    row = conn.execute(
        "SELECT expires_at FROM cooldowns WHERE user_id=? AND action=?",
        (user_id, action)
    ).fetchone()
    conn.close()
    if row:
        return row["expires_at"]
    return 0

def set_cooldown(user_id, action, seconds):
    expires = datetime.now().timestamp() + seconds
    conn = get_conn()
    conn.execute("""
        INSERT OR REPLACE INTO cooldowns (user_id, action, expires_at)
        VALUES (?, ?, ?)
    """, (user_id, action, expires))
    conn.commit()
    conn.close()

# ── Inventory Operations ──────────────────────────────────────────────────────

def add_item(user_id, item_name, rarity):
    conn = get_conn()
    existing = conn.execute(
        "SELECT id, quantity FROM inventory WHERE user_id=? AND item_name=?",
        (user_id, item_name)
    ).fetchone()
    if existing:
        conn.execute("UPDATE inventory SET quantity=quantity+1 WHERE id=?", (existing["id"],))
    else:
        conn.execute(
            "INSERT INTO inventory (user_id, item_name, rarity, acquired_at) VALUES (?,?,?,?)",
            (user_id, item_name, rarity, datetime.now().timestamp())
        )
    conn.commit()
    conn.close()

def get_inventory(user_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT item_name, rarity, quantity FROM inventory WHERE user_id=? ORDER BY rarity DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return rows

def remove_item(user_id, item_name):
    conn = get_conn()
    row = conn.execute(
        "SELECT id, quantity FROM inventory WHERE user_id=? AND item_name=?",
        (user_id, item_name)
    ).fetchone()
    if row:
        if row["quantity"] > 1:
            conn.execute("UPDATE inventory SET quantity=quantity-1 WHERE id=?", (row["id"],))
        else:
            conn.execute("DELETE FROM inventory WHERE id=?", (row["id"],))
    conn.commit()
    conn.close()

# ── Egg Operations ────────────────────────────────────────────────────────────

def add_egg(user_id):
    conn = get_conn()
    conn.execute(
        "INSERT INTO eggs (user_id, created_at) VALUES (?, ?)",
        (user_id, datetime.now().timestamp())
    )
    conn.commit()
    conn.close()

def get_active_egg(user_id):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM eggs WHERE user_id=? AND hatched=0 ORDER BY created_at ASC LIMIT 1",
        (user_id,)
    ).fetchone()
    conn.close()
    return row

def update_egg_progress(egg_id, amount):
    conn = get_conn()
    conn.execute("UPDATE eggs SET progress=progress+? WHERE egg_id=?", (amount, egg_id))
    conn.commit()
    conn.close()

def hatch_egg(egg_id):
    conn = get_conn()
    conn.execute("UPDATE eggs SET hatched=1 WHERE egg_id=?", (egg_id,))
    conn.commit()
    conn.close()

def add_companion(user_id, name, variant):
    conn = get_conn()
    conn.execute(
        "INSERT INTO companions (user_id, name, variant, created_at) VALUES (?,?,?,?)",
        (user_id, name, variant, datetime.now().timestamp())
    )
    conn.commit()
    conn.close()

def get_companion(user_id):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM companions WHERE user_id=? ORDER BY created_at DESC LIMIT 1",
        (user_id,)
    ).fetchone()
    conn.close()
    return row

# ── World Events ──────────────────────────────────────────────────────────────

def get_active_event():
    conn = get_conn()
    now = datetime.now().timestamp()
    row = conn.execute(
        "SELECT * FROM world_events WHERE active=1 AND ends_at>? ORDER BY started_at DESC LIMIT 1",
        (now,)
    ).fetchone()
    conn.close()
    return row

def start_world_event(event_type, duration_hours):
    now = datetime.now().timestamp()
    ends = now + duration_hours * 3600
    conn = get_conn()
    conn.execute("UPDATE world_events SET active=0")  # end previous
    conn.execute(
        "INSERT INTO world_events (event_type, started_at, ends_at) VALUES (?,?,?)",
        (event_type, now, ends)
    )
    conn.commit()
    conn.close()

def end_expired_events():
    now = datetime.now().timestamp()
    conn = get_conn()
    conn.execute("UPDATE world_events SET active=0 WHERE ends_at<?", (now,))
    conn.commit()
    conn.close()

# ── Faction Operations ────────────────────────────────────────────────────────

def add_faction_xp(faction_name, amount):
    conn = get_conn()
    conn.execute("UPDATE factions SET total_xp=total_xp+? WHERE faction_name=?",
                 (amount, faction_name))
    conn.commit()
    conn.close()

def get_faction_leaderboard():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM factions ORDER BY total_xp DESC").fetchall()
    conn.close()
    return rows

def reset_faction_xp():
    conn = get_conn()
    conn.execute("UPDATE factions SET total_xp=0")
    conn.commit()
    conn.close()

def join_faction(user_id, faction_name):
    old = get_user(user_id)
    if old and old["faction"]:
        conn = get_conn()
        conn.execute("UPDATE factions SET member_count=MAX(0,member_count-1) WHERE faction_name=?",
                     (old["faction"],))
        conn.commit()
        conn.close()
    conn = get_conn()
    conn.execute("UPDATE users SET faction=? WHERE user_id=?", (faction_name, user_id))
    conn.execute("UPDATE factions SET member_count=member_count+1 WHERE faction_name=?",
                 (faction_name,))
    conn.commit()
    conn.close()

# ── Social Actions ────────────────────────────────────────────────────────────

def log_social(attacker_id, target_id, action_type, result):
    conn = get_conn()
    conn.execute(
        "INSERT INTO social_actions (attacker_id, target_id, action_type, result, timestamp) VALUES (?,?,?,?,?)",
        (attacker_id, target_id, action_type, result, datetime.now().timestamp())
    )
    conn.commit()
    conn.close()

def add_revenge(victim_id, attacker_id):
    expires = datetime.now().timestamp() + 24 * 3600
    conn = get_conn()
    conn.execute(
        "INSERT INTO revenge_queue (victim_id, attacker_id, expires_at) VALUES (?,?,?)",
        (victim_id, attacker_id, expires)
    )
    conn.commit()
    conn.close()

def get_revenge_target(victim_id):
    now = datetime.now().timestamp()
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM revenge_queue WHERE victim_id=? AND used=0 AND expires_at>? ORDER BY timestamp DESC LIMIT 1",
        (victim_id, now)
    ).fetchone()
    conn.close()
    return row

def use_revenge(revenge_id):
    conn = get_conn()
    conn.execute("UPDATE revenge_queue SET used=1 WHERE id=?", (revenge_id,))
    conn.commit()
    conn.close()

# ── Stats ─────────────────────────────────────────────────────────────────────

def get_ecosystem_stats():
    conn = get_conn()
    total_users = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
    active_today = conn.execute(
        "SELECT COUNT(*) as c FROM users WHERE last_active > ?",
        (datetime.now().timestamp() - 86400,)
    ).fetchone()["c"]
    top_user = conn.execute(
        "SELECT username, xp FROM users ORDER BY xp DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return {
        "total_users": total_users,
        "active_today": active_today,
        "top_user": dict(top_user) if top_user else None,
    }
