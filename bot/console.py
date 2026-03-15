import asyncio
import threading


CONSOLE_CHAT_ID = None


async def console_input_handler(bot, handler):
    loop = asyncio.get_event_loop()

    def get_input():
        while True:
            try:
                user_input = input()
                asyncio.run_coroutine_threadsafe(process_console_input(user_input, bot, handler), loop)
            except EOFError:
                break
            except Exception as e:
                print(f"Console input error: {e}")

    thread = threading.Thread(target=get_input, daemon=True)
    thread.start()


async def process_console_input(user_input, bot, handler):
    global CONSOLE_CHAT_ID

    if not user_input.strip():
        return

    if user_input.startswith("/select "):
        try:
            chat_id = int(user_input.split()[1])
            CONSOLE_CHAT_ID = chat_id
            print(f"Selected chat: {chat_id}")
            print("You can now type commands (starting with /) or messages to send as the bot")
        except (ValueError, IndexError):
            print("Usage: /select <chat_id>")
        return

    if user_input.startswith("/chats"):
        print("\nAvailable chats:")
        async for dialog in bot.iter_dialogs(limit=20):
            print(f"  ID: {dialog.id} | {dialog.name}")
        print()
        return

    if CONSOLE_CHAT_ID is None:
        print("Select a chat first with /select <chat_id>")
        print("Use /chats to see available chats")
        return

    try:
        message = await bot.send_message(CONSOLE_CHAT_ID, user_input)
        if user_input.startswith("/"):
            await handler(message)
            print(f"Command executed in chat {CONSOLE_CHAT_ID}: {user_input}")
        else:
            print(f"Message sent to chat {CONSOLE_CHAT_ID}: {user_input}")
    except Exception as e:
        print(f"Send error: {e}")
