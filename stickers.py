from config import STICKERS

async def send_sticker(bot, chat_id, key: str):
    """Send a sticker by key name. Silently fails if key not found."""
    file_id = STICKERS.get(key)
    if file_id:
        try:
            await bot.send_sticker(chat_id=chat_id, sticker=file_id)
        except Exception:
            pass  # Never break flow over a sticker
