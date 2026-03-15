import re
import time
import datetime

from aiogram import Router, types
from aiogram.filters import Command

from config import RATE_LIMIT_WINDOW, RATE_LIMIT_MAX
from ai.model import ask_model
from utils.history import add_to_history
from utils.logging_setup import full_logger, error_logger
from bot.commands import (
    cmd_start, cmd_ping, cmd_model, cmd_mood,
    cmd_memorize, cmd_show_memory, cmd_forget,
    cmd_help, cmd_reset, cmd_prompt,
)

router = Router()
RATE_LIMIT = {}
BOT_ID: int | None = None  # set in main.py after bot.get_me()


@router.message(Command("start"))
async def _start(message: types.Message):
    await cmd_start(message)


@router.message(Command("ping"))
async def _ping(message: types.Message):
    await cmd_ping(message)


@router.message(Command("model"))
async def _model(message: types.Message):
    await cmd_model(message)


@router.message(Command("mood"))
async def _mood(message: types.Message):
    await cmd_mood(message)


@router.message(Command("memorize"))
async def _memorize(message: types.Message):
    await cmd_memorize(message)


@router.message(Command("show_memory"))
async def _show_memory(message: types.Message):
    await cmd_show_memory(message)


@router.message(Command("forget"))
async def _forget(message: types.Message):
    await cmd_forget(message)


@router.message(Command("help"))
async def _help(message: types.Message):
    await cmd_help(message)


@router.message(Command("reset"))
async def _reset(message: types.Message):
    await cmd_reset(message)


@router.message(Command("prompt"))
async def _prompt(message: types.Message):
    await cmd_prompt(message)


@router.message()
async def chat_handler(message: types.Message):
    if not message.text:
        return

    sender_id = message.from_user.id
    chat_id = message.chat.id
    username = message.from_user.username or message.from_user.first_name or f"user{sender_id}"

    now_ts = time.time()
    bucket = RATE_LIMIT.setdefault(sender_id, [])
    RATE_LIMIT[sender_id] = [t for t in bucket if now_ts - t < RATE_LIMIT_WINDOW]
    if len(RATE_LIMIT[sender_id]) >= RATE_LIMIT_MAX:
        return
    RATE_LIMIT[sender_id].append(now_ts)

    add_to_history(chat_id, username, message.text, is_bot=False)

    text_lower = message.text.lower()
    reply_to_bot = (
        message.reply_to_message is not None
        and message.reply_to_message.from_user is not None
        and message.reply_to_message.from_user.id == BOT_ID
    )
    should_respond = (
        "люми" in text_lower
        or "lumi" in text_lower
        or reply_to_bot
    )

    if should_respond:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{now}] FROM {username} in chat {chat_id}:\n{message.text}")

        clean_prompt = re.sub(r'(?i)\bлюми\b|\blumi\b', '', message.text).strip()

        try:
            reply = await ask_model(clean_prompt, chat_id, username)
            await message.reply(reply)
            add_to_history(chat_id, "Люми", reply, is_bot=True)

            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{now_str}] LUMI ANSWERED in chat {chat_id}:\n{reply}")
            full_logger.info(f"{username} ({chat_id}): {message.text}")
            full_logger.info(f"Lumi ({chat_id}): {reply}")
        except Exception as e:
            error_logger.exception(f"Error responding in {chat_id}: {e}")
            await message.reply("⚠️ Произошла ошибка при обработке сообщения.")
