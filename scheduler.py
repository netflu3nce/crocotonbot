import random
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from config import GROUP_ID, WORLD_EVENTS
from db.database import end_expired_events, reset_faction_xp, get_faction_leaderboard
from systems.hunger import tick_hunger

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

def setup_scheduler(bot):
    # ── Hunger tick every 2 hours ──────────────────────────────────────────
    async def hunger_job():
        try:
            affected = tick_hunger()
            if affected:
                logger.info(f"Hunger ticked for {len(affected)} users")
        except Exception as e:
            logger.error(f"Hunger job error: {e}")

    scheduler.add_job(hunger_job, IntervalTrigger(hours=2), id="hunger_tick")

    # ── Random world event every 6-12 hours (randomized) ──────────────────
    async def event_job():
        try:
            end_expired_events()
            from db.database import get_active_event
            if get_active_event():
                return  # Event already running

            # 40% chance to trigger an event each run
            if random.random() < 0.4:
                from handlers.events import announce_random_event
                await announce_random_event(bot, GROUP_ID)
        except Exception as e:
            logger.error(f"Event job error: {e}")

    scheduler.add_job(event_job, IntervalTrigger(hours=6), id="world_event")

    # ── Weekly faction reset (every Monday at midnight) ───────────────────
    async def faction_reset_job():
        try:
            rows = get_faction_leaderboard()
            winner = rows[0] if rows else None
            reset_faction_xp()
            if winner:
                await bot.send_message(
                    chat_id=GROUP_ID,
                    text=(
                        f"🏆 *WEEKLY TERRITORY WAR ENDED*\n"
                        f"━━━━━━━━━━━━━\n"
                        f"👑 *{winner['faction_name']}* dominated the swamp!\n"
                        f"⚡ {winner['total_xp']:,} XP earned\n"
                        f"👥 {winner['member_count']} warriors\n\n"
                        f"_New war begins now. Claim your territory._"
                    ),
                    parse_mode="Markdown"
                )
        except Exception as e:
            logger.error(f"Faction reset job error: {e}")

    scheduler.add_job(
        faction_reset_job,
        CronTrigger(day_of_week="mon", hour=0, minute=0),
        id="faction_reset"
    )

    # ── Daily activity reminder (random time) ─────────────────────────────
    async def daily_nudge():
        try:
            messages = [
                "🐊 The swamp is calling. Have you hunted today?",
                "🌿 Prey moves through the reeds. Your croco grows hungry.",
                "⚡ Streaks don't maintain themselves. /hunt",
                "🔥 Territory wars are ongoing. Your faction needs you.",
                "👑 Someone just climbed the leaderboard. Are you watching?",
            ]
            msg = random.choice(messages)
            await bot.send_message(chat_id=GROUP_ID, text=msg)
        except Exception as e:
            logger.error(f"Daily nudge error: {e}")

    scheduler.add_job(
        daily_nudge,
        CronTrigger(hour=random.choice([9, 12, 15, 18, 20]), minute=0),
        id="daily_nudge"
    )

    logger.info("Scheduler jobs registered.")
