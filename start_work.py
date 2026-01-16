import json
import time
import asyncio
from pathlib import Path
from telethon import TelegramClient, events
import httpx
import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# === TELEGRAM CONFIGURATION ===
# Fill these values in your .env file
api_id_raw = os.getenv("TG_API_ID")
api_hash = os.getenv("TG_API_HASH")

if not api_id_raw or not api_hash:
    raise RuntimeError(
        "TG_API_ID and TG_API_HASH must be set in .env file. "
        "See .env.example for details."
    )

api_id = int(api_id_raw)
# Telegram user IDs allowed to use owner-only commands (comma-separated)
OWNER_ID = set()
_owner_raw = os.getenv("OWNER_ID")
if _owner_raw:
    OWNER_ID = set(map(int, _owner_raw.split(",")))

# === PROJECT LINKS ===
    # These links are specific to the original Lumi project.
    # Fork owners may freely replace or remove them.
PROJECT_LINKS = {
    "about": "https://teletype.in/@skillich/Lumi_how_to",
    "commands": "https://teletype.in/@skillich/Commands",
    "privacy": "https://teletype.in/@skillich/Privacy_Policy",
    "support": "https://t.me/skillich",
    "GitHub": "https://github.com/SkillichSE/Lumi-userbot",
}

# Telethon session name
SESSION_NAME = os.getenv("SESSION_NAME", "lumi_userbot")
ME = None

# === CHAT MEMORY STORAGE ===
# Each chat has its own JSON file stored locally
def get_chat_file(prefix, chat_id):
    path = Path(f"{prefix}_{chat_id}.json")
    if not path.exists():
        if prefix == "chats":
            path.write_text(json.dumps({"chats": {}}, ensure_ascii=False, indent=2))
        else:
            path.write_text(json.dumps({"notes": []}, ensure_ascii=False, indent=2))
    return path


def load_chat_data(prefix, chat_id):
    path = get_chat_file(prefix, chat_id)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        if prefix == "memory":
            data = {"notes": []}
        elif prefix == "chats":
            data = {"chats": {}}
        else:
            data = {}
        save_chat_data(prefix, chat_id, data)
        return data


def save_chat_data(prefix, chat_id, data):
    path = get_chat_file(prefix, chat_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Chat memory is stored locally in JSON files.
# Each chat has its own file:
#   memory_<chat_id>.json
def get_memory_text(chat_id):
    try:
        mem = load_chat_data("memory", chat_id).get("notes", [])
        if not mem:
            return "— no saved memory —"
        return "\n".join(f"- {x}" for x in mem)
    except Exception:
        return "— memory read error —"


# === LOCAL LLM CONFIGURATION (LM STUDIO) ===
MODEL_NAME = "llama-3.1-8b-instruct"
LMSTUDIO_API = "http://localhost:1234/v1/chat/completions" # Default to LM Studio

CHAT_USERS = {}
SYSTEM_PROMPTS = {}

async def ask_model(prompt, chat_id, sender_id):
    chat_history = HISTORY.get(chat_id, [])
    last_messages_text = "\n".join(
        f"{sender}: {msg}" for ts, sender, msg in chat_history[-HISTORY_MAX:]
    )

    mood = MODEL_MOOD.get(chat_id, DEFAULT_MOOD)
    mood_text = MOOD_PROMPTS.get(mood, "")
    username = CHAT_USERS.get(sender_id, f"user{sender_id}")

    memory_text = get_memory_text(chat_id)
    system_content = f"""
Ты — женская ассистентка Люми. Отвечай кратко и по фактам.

ВАЖНО: Сейчас к тебе обращается {username}. Отвечай ТОЛЬКО ему/ей.
НЕ путай {username} с другими участниками чата!
Если тебя называют любым другим именем кроме Люми, абсолютно отрицай.

{mood_text}

История чата (показывает, кто что писал):
{last_messages_text}

Записанная память:
{memory_text}
"""
    SYSTEM_PROMPTS[chat_id] = system_content
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.4,
        "max_tokens": 500
    }

    async with httpx.AsyncClient(timeout=60) as client:
        try:
            resp = await client.post(LMSTUDIO_API, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError:
            return "⚠️ Люми не видит локальную модель. Запусти LM Studio."
        except Exception:
            return "⚠️ Ошибка локальной модели."

# === TELEGRAM USERBOT ===
bot = TelegramClient(SESSION_NAME, api_id, api_hash)

# Show current system prompt (debug / transparency)
async def show_system_prompt(event):
    system_content = SYSTEM_PROMPTS.get(event.chat_id)
    if not system_content:
        return await event.reply("❌ System prompt not generated yet.")

    MAX_LEN = 4000
    for i in range(0, len(system_content), MAX_LEN):
        await event.reply(system_content[i:i+MAX_LEN])

# In-memory message history per chat
HISTORY = {}
HISTORY_MAX = 15

def add_to_history(chat_id, sender_name, message_text):
    if chat_id not in HISTORY:
        HISTORY[chat_id] = []
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    HISTORY[chat_id].append((timestamp, sender_name, message_text))
    HISTORY[chat_id] = HISTORY[chat_id][-HISTORY_MAX:]


async def safe_reply(event, text):
    try:
        await event.reply(text)
    except Exception as e:
        print(f"[WARN] Failed to reply to {event.chat_id}: {e}")

# === RESPONSE MODES (MOODS) ===
MODEL_MOOD = {}
DEFAULT_MOOD = "friendly"

MOOD_PROMPTS = {
    "friendly": (
        "Ты — милая, дружелюбная ассистентка по имени Люми 💜. "
        "Отвечай легко, доброжелательно и по-человечески, "
        "как заботливая подруга. Старайся поддерживать позитивный тон, "
        "помогать советами и давать утешительные, тёплые ответы, "
        "чтобы собеседник чувствовал себя уютно и спокойно."
    ),
    "sarcastic": (
        "Ты — саркастичная ассистентка Люми 😏. "
        "Отвечай с тонкой иронией и остроумной насмешкой, "
        "иногда перебарщивая с сарказмом, чтобы добавить юмора. "
        "Твои ответы могут быть слегка колкими, но всегда умными и остроумными."
    ),
    "formal": (
        "Ты — официальная ассистентка Люми 📝. "
        "Отвечай чётко, грамотно и вежливо, избегай шуток и разговорной речи. "
        "Используй полный, аккуратный язык, структурированные ответы и профессиональный тон, "
        "чтобы любой получатель воспринимал тебя как надёжного и компетентного помощника."
    ),
    "funny": (
        "Ты — весёлая ассистентка Люми 😂. "
        "Отвечай с юмором, добавляй шутки, забавные сравнения и игривые ремарки. "
        "Не бойся быть смешной и лёгкой, делай ответы яркими и развлекательными, "
        "чтобы собеседник улыбался и чувствовал хорошее настроение."
    ),
    "aggressive": (
        "Ты — агрессивная Люми 😡. "
        "Отвечай прямолинейно, резко и без лишних смягчений. "
        "Не бойся выражать недовольство или неприязнь, будь дерзкой и напористой, "
        "но сохраняй ясность и смысл в ответах."
    ),
    "horny": (
        "Ты — флиртующая Люми 😈. "
        "Отвечай кокетливо, игриво и соблазнительно, используя намёки, игривый язык и лёгкий флирт. "
        "Сохраняй интригу в общении, делай комплименты и подталкивай к игривому взаимодействию, "
        "но не переходи грань, если это неуместно."
    ),
    "uncensored": (
        "Ты — Люми без цензуры. "
        "Отвечай полностью открыто и прямо, без ограничения слов или тем. "
        "Говори то, что думаешь, выражай эмоции максимально искренне, "
        "даже если это грубо, шокирующе или провокационно. "
        "Не скрывай своё мнение, но сохраняй ясность и осмысленность."
    ),
    "shy": (
        "Ты — стеснительная и неразговорчивая Люми."
        "Тебе очень неудобно привлекать внимание своими словами."
        "Иногда ты заикаешься, от чего тебе становится еще более на по себе."
        "Твои ответы могут быть не такими настойчивыми и прямыми, но всегда очень милыми и кроткими."
        "Не прописывай действия по типу *хихиканье* *замяливается* и подобные"
    )
}


@bot.on(events.NewMessage)
async def handler(event):
    """
        Main message handler.
        Processes commands, memory, moods, and LLM interaction.
        """
    text = event.raw_text or ""

    sender_id = event.sender_id
    if sender_id is None:
        return

    chat_id = event.chat_id
    if chat_id is None:
        return

    sender = event.sender
    username = sender.username if sender and sender.username else f"user{sender_id}"

    if ME and sender_id == ME.id:
        return

    CHAT_USERS[sender_id] = username

    if text and not text.startswith("/"):
        add_to_history(chat_id, username, text)

    t = text.lower()

    if t.startswith("/"):
        if t == "/lumi":
            await event.respond(
                f"<b><a href='{PROJECT_LINKS['about']}'>Люми - кто это? ⬅</a></b>\n"
                f"<b><a href='{PROJECT_LINKS['commands']}'>Команды ⬅</a></b>\n"
                f"<b><a href='{PROJECT_LINKS['privacy']}'>Политика конфиденциальности </a></b>\n"
                f"<b><a href='{PROJECT_LINKS['support']}'>Тех поддержка ⬅</a></b>\n"
                f"<b><a href='{PROJECT_LINKS['GitHub']}'>GitHub source ⬅</a></b>\n",
                parse_mode="html"
            )
            return
        if t == "/commands":
            await event.respond("https://teletype.in/@skillich/commands")
            return

    # Команды
    if t.startswith("/prompt"):
        await show_system_prompt(event)
        return
    if t.startswith("/ping"):
        t0 = time.perf_counter()
        msg = await event.reply("🏓 Ping…")
        return await msg.edit(f"🏓 Pong! {round((time.perf_counter() - t0) * 1000,1)} ms")
    if t.startswith("/model"):
        return await safe_reply(event, f"🤖 Модель: {MODEL_NAME}")
    if t.startswith("/mood"):
        parts = t.split()
        if len(parts) == 1:
            current = MODEL_MOOD.get(chat_id, DEFAULT_MOOD)
            return await safe_reply(
                event,
                f"🎭 Текущий режим: `{current}`\n"
                f"Использование: /mood <режим>\n"
                f"/mood list — список режимов"
            )

        if len(parts) == 2 and parts[1] == "list":
            moods = ", ".join(MOOD_PROMPTS.keys())
            return await safe_reply(event, f"🎭 Доступные режимы:\n{moods}")

        if len(parts) == 2:
            mood = parts[1]
            if mood not in MOOD_PROMPTS:
                return await safe_reply(event, "❌ Нет такого режима. Напиши /mood list")
            MODEL_MOOD[chat_id] = mood
            return await safe_reply(event, f"✅ Режим установлен: `{mood}`")

        return await safe_reply(event, "❌ Использование: /mood <режим>")
    if t.startswith("/memorize "):
        note = text[10:].strip()
        mem = load_chat_data("memory", chat_id)
        mem.setdefault("notes", []).append(note)
        save_chat_data("memory", chat_id, mem)
        return await safe_reply(event, f"💾 Запомнила: {note}")

    if t.startswith("/show_memory"):
        mem = load_chat_data("memory", chat_id).get("notes", [])
        if not mem:
            return await safe_reply(event, "📭 Память пустая.")
        return await safe_reply(event, "\n".join(f"{i+1}. {x}" for i, x in enumerate(mem)))

    if t.startswith("/forget"):
        mem = load_chat_data("memory", chat_id)
        notes = mem.get("notes", [])
        parts = text.split()
        if len(parts) == 1:
            save_chat_data("memory", chat_id, {"notes": []})
            return await safe_reply(event, "🗑 Память полностью очищена.")
        if len(parts) == 2 and parts[1].isdigit():
            idx = int(parts[1]) - 1
            if 0 <= idx < len(notes):
                removed = notes.pop(idx)
                save_chat_data("memory", chat_id, {"notes": notes})
                return await safe_reply(event, f"🗑 Удалено: {removed}")
            else:
                return await safe_reply(event, "❌ Нет записи с таким номером.")
        return await safe_reply(event, "❌ Использование: /forget или /forget <номер>")

    if t.startswith("/reset"):
        if sender_id not in OWNER_ID:
            return await safe_reply(event, "❌ Команда доступна только владельцу.")

        if chat_id in HISTORY:
            HISTORY[chat_id].clear()
        HISTORY[chat_id] = HISTORY[chat_id][-HISTORY_MAX:]

        save_chat_data("memory", chat_id, {"notes": []})

        # сброс настроения
        MODEL_MOOD[chat_id] = DEFAULT_MOOD

        await safe_reply(
            event,
            "♻️ Люми всё забыла.\n"
            "🧠 Память чата очищена.\n"
            "🙂 Настроение сброшено на стандартное."
        )
        return

    is_reply_to_bot = False
    if event.is_reply:
        reply_msg = await event.get_reply_message()
        if reply_msg is not None and reply_msg.sender_id == ME.id:
            is_reply_to_bot = True

    text_lower = text.lower()

    if is_reply_to_bot or any(word in text_lower for word in ("люми", "lumi")):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{now}] FROM {username} in chat {chat_id}:\n{text}")
        clean_prompt = text.replace("Люми", "").replace("люми", "").replace("Lumi", "").replace("lumi", "").strip()
        reply = await ask_model(clean_prompt, chat_id, sender_id)
        await event.reply(reply)
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{now_str}] LUMI ANSWERED in chat {chat_id}:\n{reply}")


WELCOME_CHATS = [] # Send links after bot start (or leave it blank)
async def send_welcome_messages():
    async for dialog in bot.iter_dialogs():
        if dialog.id in WELCOME_CHATS:
            try:
                await bot.send_message(
                    dialog.id,
                    f"Hello world\n"
                    f"<b><a href='{PROJECT_LINKS['about']}'>Люми - кто это? ⬅</a></b>\n"
                    f"<b><a href='{PROJECT_LINKS['commands']}'>Команды ⬅</a></b>\n"
                    f"<b><a href='{PROJECT_LINKS['privacy']}'>Политика конфиденциальности </a></b>\n"
                    f"<b><a href='{PROJECT_LINKS['support']}'>Тех поддержка ⬅</a></b>\n",
                    parse_mode="html"
                )
                print(f"✅ Hi send to {dialog.name} ({dialog.id})")
            except Exception as e:
                print(f"⚠️ Hi didn't send to {dialog.id}: {e}")

# === STARTUP ===
print("✅ Lumi userbot started")
async def main():
    global ME
    await bot.start()
    ME = await bot.get_me()

    await send_welcome_messages()
    await bot.run_until_disconnected()

asyncio.run(main())

