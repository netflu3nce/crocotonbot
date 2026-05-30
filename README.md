# 🐊 CrocoBot — Telegram Engagement System

A full gamified Telegram bot ecosystem for the Croco TON memecoin community.

---

## 🚀 Deploy to Render + GitHub

### Step 1 — GitHub
1. Create a new GitHub repo (e.g. `croco-bot`)
2. Push all files to it

```bash
git init
git add .
git commit -m "croco bot launch"
git remote add origin https://github.com/YOURUSERNAME/croco-bot.git
git push -u origin main
```

### Step 2 — BotFather Setup
1. Go to @BotFather on Telegram
2. `/newbot` → name it → get your BOT_TOKEN
3. `/setprivacy` → select your bot → `Disable` (so it reads group messages)

### Step 3 — Render Deployment
1. Go to https://render.com → New Web Service
2. Connect your GitHub repo
3. Set these environment variables:
   - `BOT_TOKEN` = your token from BotFather
   - `WEBHOOK_URL` = your Render URL (e.g. `https://croco-bot.onrender.com`)
   - `PORT` = `8080`
4. Render auto-detects `render.yaml` and creates a 1GB persistent disk at `/data`
5. Deploy → wait for build to complete

### Step 4 — UptimeRobot
1. Go to https://uptimerobot.com
2. Add monitor → HTTP(s)
3. URL: `https://your-render-url.onrender.com/health`
4. Interval: every 5 minutes
5. This keeps the bot from sleeping

---

## ⚙️ Bot Setup in Group

1. Add bot to your group (`@Crocotoncommunity`)
2. Make it **admin** (so it can send stickers + see messages)
3. Set `/setprivacy` to **Disabled** in BotFather

---

## 📋 Commands

| Command | Description |
|---------|-------------|
| `/hunt` | Hunt every 8 hours |
| `/profile` | View your croco profile |
| `/inventory` | Check your items |
| `/leaderboard` | Top 10 crocos |
| `/factions` | Faction standings |
| `/ambush @user` | Ambush another croco (12h CD) |
| `/protect` | Shield yourself 5 hours (24h CD) |
| `/revenge` | Strike back within 24h |
| `/gift @user item` | Gift an item |
| `/join <faction>` | Join a faction |
| `/event` | Check active world event |
| `/admin` | Admin controls (restricted) |

---

## 🌍 Factions
- Black Swamp
- Deep Waters
- Red Marsh
- Fog Hollow

---

## 🔴 Admin Commands
`/admin stats` — ecosystem overview
`/admin event <type>` — trigger world event
`/admin exile @user <hours>` — exile a user
`/admin spawn boss` — spawn legendary boss
`/admin reset_factions` — end weekly territory war
`/admin give @user <item> <rarity>` — grant item

Event types: `blood_moon`, `drought`, `mutation_storm`, `swamp_flood`, `feeding_frenzy`

---

## 📁 File Structure
```
croco-bot/
├── bot.py              # Main entry point
├── keep_alive.py       # Flask health check
├── scheduler.py        # APScheduler jobs
├── config.py           # All constants + sticker IDs
├── handlers/
│   ├── hunt.py         # /hunt command
│   ├── profile.py      # /profile /leaderboard /factions
│   ├── social.py       # /ambush /protect /revenge /gift /join
│   ├── events.py       # World events
│   └── admin.py        # Admin commands
├── systems/
│   ├── xp.py           # XP + rank logic
│   ├── hunger.py       # Hunger decay
│   ├── inventory.py    # Item drops
│   ├── eggs.py         # Egg + companion system
│   ├── corruption.py   # Corruption mechanic
│   └── stickers.py     # Sticker sender util
├── db/
│   └── database.py     # SQLite ORM layer
├── requirements.txt
├── Procfile
└── render.yaml
```
