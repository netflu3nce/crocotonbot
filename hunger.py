from datetime import datetime
from db.database import get_conn, get_user

HUNGER_THRESHOLD_HOURS = 16  # start getting hungry after 16h inactivity

def tick_hunger():
    """Called by scheduler every 2 hours. Increases hunger for inactive users."""
    now = datetime.now().timestamp()
    cutoff = now - HUNGER_THRESHOLD_HOURS * 3600

    conn = get_conn()
    # Get all users who haven't hunted recently and aren't at max hunger
    rows = conn.execute(
        "SELECT user_id, hunger FROM users WHERE last_hunt < ? AND hunger < 10",
        (cutoff,)
    ).fetchall()

    for row in rows:
        conn.execute(
            "UPDATE users SET hunger=MIN(hunger+1, 10) WHERE user_id=?",
            (row["user_id"],)
        )
    conn.commit()
    conn.close()
    return [row["user_id"] for row in rows]

def reset_hunger(user_id):
    conn = get_conn()
    conn.execute("UPDATE users SET hunger=0 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def get_hunger_message(hunger: int) -> str:
    messages = {
        0: None,
        1: "your croco is a little restless...",
        2: "your croco hasn't eaten in a while 👀",
        3: "⚠️ your croco grows restless in the swamp. XP gains reduced.",
        4: "⚠️ hunger spreading. your croco is weakening.",
        5: "🔴 your croco is starving. rewards at 50% efficiency.",
        6: "🔴 the swamp is forgetting your name.",
        7: "💀 your croco is barely moving.",
        8: "💀 legend fading. hunt before it's too late.",
        9: "☠️ on the edge of exile. one more absence and you lose your streak.",
        10: "☠️ your croco has gone fully dark. max hunger. bare minimum rewards.",
    }
    return messages.get(min(hunger, 10))
