import datetime
import time

from telethon import events

from config import RATE_LIMIT_WINDOW, RATE_LIMIT_MAX
from ai.model import ask_model
from utils.history import add_to_history
from bot.commands import (
    safe_reply, cmd_ping, cmd_model, cmd_mood, cmd_memorize,
    cmd_show_memory, cmd_forget, cmd_help, cmd_reset,
    cmd_set_prompt, cmd_prompt,
)

RATE_LIMIT = {}
ME = None


def register(bot):
    @bot.on(events.NewMessage)
    async def handler(event):
        sender_id = event.sender_id
        chat_id = event.chat_id
        text = event.text or ""

        if not text:
            return

        now_ts = time.time()
        bucket = RATE_LIMIT.setdefault(sender_id, [])
        RATE_LIMIT[sender_id] = [t for t in bucket if now_ts - t < RATE_LIMIT_WINDOW]
        if len(RATE_LIMIT[sender_id]) >= RATE_LIMIT_MAX:
            return
        RATE_LIMIT[sender_id].append(now_ts)

        sender = await event.get_sender()
        username = getattr(sender, "username", None) or getattr(sender, "first_name", "Unknown")

        if not text.startswith("/"):
            add_to_history(chat_id, username, text, is_bot=False)

        t = text.lower().strip()

        if t.startswith("/ping"):
            return await cmd_ping(event)
        if t.startswith("/model"):
            return await cmd_model(event)
        if t.startswith("/mood"):
            return await cmd_mood(event, text)
        if t.startswith("/memorize "):
            return await cmd_memorize(event, text)
        if t.startswith("/show_memory"):
            return await cmd_show_memory(event)
        if t.startswith("/forget"):
            return await cmd_forget(event, text)
        if t.startswith("/help"):
            return await cmd_help(event)
        if t.startswith("/reset"):
            return await cmd_reset(event, sender_id)
        if t.startswith("/set_prompt "):
            return await cmd_set_prompt(event, text, sender_id)
        if t.startswith("/prompt"):
            return await cmd_prompt(event)

        is_reply_to_bot = False
        if event.is_reply:
            reply_msg = await event.get_reply_message()
            if reply_msg is not None and reply_msg.sender_id == ME.id:
                is_reply_to_bot = True

        text_lower = text.lower()
        should_respond = (
            is_reply_to_bot
            or "люми" in text_lower
            or "lumi" in text_lower
        )

        if should_respond:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{now}] FROM {username} in chat {chat_id}:\n{text}")

            clean_prompt = text.lower().replace("люми", "").replace("lumi", "").strip()

            reply = await ask_model(clean_prompt, chat_id, username)
            await event.reply(reply)
            add_to_history(chat_id, "Люми", reply, is_bot=True)

            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{now_str}] LUMI ANSWERED in chat {chat_id}:\n{reply}")