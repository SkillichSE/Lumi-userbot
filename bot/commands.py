from config import PROJECT_LINKS, OWNER_ID
from ai.model import MODEL_NAME, MODEL_MOOD, SYSTEM_PROMPTS
from ai.moods import MOOD_PROMPTS, DEFAULT_MOOD
from utils.storage import load_chat_data, save_chat_data
from utils.history import LUMI_HISTORY


async def safe_reply(event, text):
    try:
        await event.reply(text)
    except Exception as e:
        print(f"[WARN] failed to reply in {event.chat_id}: {e}")


async def cmd_ping(event):
    import time
    start = time.time()
    msg = await event.reply("🏓 Pong!")
    latency = int((time.time() - start) * 1000)
    await msg.edit(f"🏓 Pong! {latency} ms")


async def cmd_model(event):
    await safe_reply(event, f"🤖 Модель: {MODEL_NAME}")


async def cmd_mood(event, text):
    chat_id = event.chat_id
    parts = text.split(maxsplit=1)
    if len(parts) == 1:
        current = MODEL_MOOD.get(chat_id, DEFAULT_MOOD)
        return await safe_reply(event, f"🎭 Текущий режим: {current}")
    mood_input = parts[1].strip().lower()
    if mood_input == "list":
        moods_list = "\n".join(f"• {m}" for m in MOOD_PROMPTS.keys())
        return await safe_reply(event, f"🎭 Доступные режимы:\n{moods_list}")
    if mood_input in MOOD_PROMPTS:
        MODEL_MOOD[chat_id] = mood_input
        return await safe_reply(event, f"✅ Режим изменён на: {mood_input}")
    await safe_reply(event, "❌ Неизвестный режим. Используй /mood list")


async def cmd_memorize(event, text):
    chat_id = event.chat_id
    note_text = text[10:].strip()
    if not note_text:
        return await safe_reply(event, "❌ Укажите текст заметки.")
    mem = load_chat_data("memory", chat_id)
    notes = mem.get("notes", [])
    notes.append(note_text)
    save_chat_data("memory", chat_id, {"notes": notes})
    await safe_reply(event, f"💾 Запомнила: {note_text}")


async def cmd_show_memory(event):
    chat_id = event.chat_id
    mem = load_chat_data("memory", chat_id)
    notes = mem.get("notes", [])
    if not notes:
        return await safe_reply(event, "🧠 Память пуста.")
    msg = "🧠 <b>Память:</b>\n" + "\n".join(f"{i + 1}. {n}" for i, n in enumerate(notes))
    await safe_reply(event, msg)


async def cmd_forget(event, text):
    chat_id = event.chat_id
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
        return await safe_reply(event, "❌ Нет записи с таким номером.")
    await safe_reply(event, "❌ Использование: /forget или /forget <номер>")


async def cmd_help(event):
    await safe_reply(
        event,
        "<b>КОМАНДЫ:</b>\n\n"
        "<b>/mood</b> — показать текущий режим\n"
        "<b>/mood &lt;режим&gt;</b> — установить режим (friendly, sarcastic, formal…)\n"
        "<b>/mood list</b> — список всех режимов\n"
        "<b>/model</b> — показать текущую модель\n"
        "<b>/memorize &lt;заметка&gt;</b> — сохранить заметку в память\n"
        "<b>/show_memory</b> — показать заметки\n"
        "<b>/forget</b> — очистить всю память\n"
        "<b>/forget &lt;номер&gt;</b> — удалить конкретную заметку\n"
        "<b>/reset</b> — очистить историю и память (только владелец)\n"
        "<b>/ping</b> — проверить задержку\n"
        "<b>/prompt</b> — показать текущий system prompt\n"
        "<b>/set_prompt &lt;текст&gt;</b> — изменить system prompt (только владелец)\n\n"
        f"<b><a href='{PROJECT_LINKS['about']}'>Люми — кто это?</a></b>\n"
        f"<b><a href='{PROJECT_LINKS['github']}'>GitHub</a></b>\n"
        f"<b><a href='{PROJECT_LINKS['support']}'>Тех поддержка</a></b>"
    )


async def cmd_reset(event, sender_id):
    if sender_id not in OWNER_ID:
        return await safe_reply(event, "❌ Команда доступна только владельцу.")
    chat_id = event.chat_id
    if chat_id in LUMI_HISTORY:
        LUMI_HISTORY[chat_id].clear()
    LUMI_HISTORY.setdefault(chat_id, [])
    save_chat_data("memory", chat_id, {"notes": []})
    MODEL_MOOD[chat_id] = DEFAULT_MOOD
    await safe_reply(
        event,
        "♻️ Люми всё забыла.\n"
        "🧠 Память чата очищена.\n"
        "🙂 Настроение сброшено на стандартное."
    )


async def cmd_set_prompt(event, text, sender_id):
    if sender_id not in OWNER_ID:
        return await safe_reply(event, "❌ Команда доступна только владельцу.")
    new_prompt = text[12:].strip()
    if not new_prompt:
        return await safe_reply(event, "❌ Укажите текст промпта после команды.")
    SYSTEM_PROMPTS[event.chat_id] = new_prompt
    await safe_reply(event, f"✅ Системный промпт обновлён! Длина: {len(new_prompt)} символов.")


async def cmd_prompt(event):
    system_content = SYSTEM_PROMPTS.get(event.chat_id)
    if not system_content:
        return await event.reply("❌ System prompt ещё не сгенерирован.")
    MAX_LEN = 4000
    for i in range(0, len(system_content), MAX_LEN):
        await event.reply(system_content[i:i + MAX_LEN])
