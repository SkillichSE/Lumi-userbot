import asyncio
import os

from telethon import TelegramClient

from config import API_ID, API_HASH, SESSION_NAME, PROJECT_LINKS, WELCOME_CHATS
from ai.search import load_classifier
from ai.model import cleanup_http
from bot import handler as handler_module
from bot.console import console_input_handler

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["DISABLE_TQDM"] = "1"
os.environ["TQDM_DISABLE"] = "1"

bot = TelegramClient(SESSION_NAME, API_ID, API_HASH)


async def send_welcome_messages():
    async for dialog in bot.iter_dialogs():
        if dialog.id in WELCOME_CHATS:
            try:
                await bot.send_message(
                    dialog.id,
                    f"Hello world\n"
                    f"<b><a href='{PROJECT_LINKS['about']}'>Люми - кто это? </a></b>\n"
                    f"<b><a href='{PROJECT_LINKS['commands']}'>Команды ⬅</a></b>\n"
                    f"<b><a href='{PROJECT_LINKS['github']}'>GitHub </a></b>\n"
                    f"<b><a href='{PROJECT_LINKS['support']}'>Тех поддержка ⬅</a></b>\n"
                    f"<b><a href='{PROJECT_LINKS['site']}'>Сайт </a></b>\n",
                    parse_mode="html"
                )
                print(f"Welcome message sent to {dialog.name} ({dialog.id})")
            except Exception as e:
                print(f"Welcome message failed for {dialog.id}: {e}")


async def main():
    await bot.start()
    me = await bot.get_me()

    handler_module.ME = me
    handler_module.register(bot)

    await console_input_handler(bot, handler_module.handler if hasattr(handler_module, "handler") else None)

    print("\nConsole commands:")
    print("  /chats - list available chats")
    print("  /select <chat_id> - select a chat")
    print("  After selecting a chat:")
    print("    /command - send a command to the chat")
    print("    text - send a message as the bot\n")

    await send_welcome_messages()

    try:
        await bot.run_until_disconnected()
    finally:
        await cleanup_http()


print("Lumi userbot started", flush=True)
load_classifier()
asyncio.run(main())
