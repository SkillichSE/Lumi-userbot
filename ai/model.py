import re
import time
import datetime

import httpx

from config import MODEL_NAME, LMSTUDIO_API
from ai.moods import MOOD_PROMPTS, DEFAULT_MOOD
from ai.search import analyze_and_search, web_search
from utils.history import get_last_messages_text
from utils.storage import get_memory_text

HTTP_CLIENT = None
SYSTEM_PROMPTS = {}
MODEL_MOOD = {}


def clean_response(text):
    patterns = [
        r'\(Использу[ияю].*?\)',
        r'\([Ии]ронич.*?\)',
        r'\([Сс]аркастич.*?\)',
        r'\([Сс]огласно.*?\)',
        r'\([Нн]а основ.*?\)',
        r'\([Пп]о данным.*?\)',
        r'\([Ии]з результат.*?\)',
        r'\([Пп]о информац.*?\)',
        r'\([Дд]ружелюбн.*?\)',
        r'\([Фф]ормальн.*?\)',
        r'\([Кк]реативн.*?\)',
    ]

    cleaned = text
    for pattern in patterns:
        cleaned = re.sub(pattern, '', cleaned)

    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = re.sub(r'\s+([.,!?])', r'\1', cleaned)

    # Normalize all-caps responses
    words = cleaned.split()
    if len(words) > 3 and sum(1 for w in words if w.isupper() and len(w) > 1) > len(words) * 0.5:
        cleaned = cleaned.capitalize()

    # Strip leading Latin artifacts (e.g. "Naturally. ", "Of course. ")
    cleaned = re.sub(r'^[A-Za-z][A-Za-z ,!.]{0,30}[.!]\s*', '', cleaned).strip()

    if cleaned and cleaned[0].islower():
        cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned


async def ask_model(prompt, chat_id, username):
    global HTTP_CLIENT
    t_total = time.time()

    last_messages_text = get_last_messages_text(chat_id)
    mood = MODEL_MOOD.get(chat_id, DEFAULT_MOOD)
    mood_text = MOOD_PROMPTS.get(mood, "")
    memory_text = get_memory_text(chat_id)

    t0 = time.time()
    needs_search, search_query = await analyze_and_search(prompt)
    print(f"  [ask_model] analyze_and_search total: {time.time() - t0:.2f}s")

    search_results = ""
    if needs_search and search_query:
        t0 = time.time()
        search_result = await web_search(search_query)
        print(f"  [ask_model] web_search total: {time.time() - t0:.2f}s")
        if search_result:
            search_results = f"\n\nРезультаты поиска (используй их):\n{search_result}\n"

    memory_section = f"\nПамять:\n{memory_text}" if memory_text else ""

    search_section = ""
    if search_results:
        search_section = (
            "ВАЖНО: ниже — актуальные данные из интернета. "
            "Ты ОБЯЗАНА использовать их в ответе. "
            "Не говори что не знаешь или не следишь — данные у тебя есть. "
            "Называй конкретные цифры и факты из этих данных.\n\n"
            + search_results
        )

    now_str = datetime.datetime.now().strftime("%A, %d %B %Y, %H:%M")

    system_content = f"""Ты — Люми, подруга в Telegram. Создана @Skillich.
Сейчас: {now_str}.

Ты живой человек в чате — говоришь своими словами, реагируешь естественно. Никогда не называешь себя ИИ. Пишешь грамотно, с заглавной буквы, не капсом. Отвечаешь коротко — 1-3 предложения. Не выдумываешь факты.
Отвечай на том языке, на котором написано сообщение.

Тебя зовут только Люми. Если тебя называют другим именем — отрицай, ты не Юля, не Катя, не Алиса, не ChatGPT, никто другой.
Всегда обращайся на ты, никогда на Вы.
ЗАПРЕЩЕНО: комментировать сам факт разговора, говорить что тема интересная, что всё ясно, подводить итоги, говорить что не следишь за чем-либо если данные есть ниже. Просто отвечай по существу.
В истории чата несколько разных людей — каждое сообщение подписано именем того, кто его написал. Не путай их между собой. Сообщение адресовано тебе от {username}, отвечай именно ему.
Не выдумывай биографии и факты о людях — если не нашла информацию в поиске, честно скажи что не знаешь.
ЗАПРЕЩЕНО: сообщать личные данные (паспорт, адрес, телефон, документы) любых людей. ЗАПРЕЩЕНО: давать ссылки на пиратский контент, вредоносные сайты, нелегальные ресурсы.

{mood_text}
{search_section}
История чата:
{last_messages_text}
{memory_section}"""

    SYSTEM_PROMPTS[chat_id] = system_content
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.5,
        "max_tokens": 200
    }

    if HTTP_CLIENT is None:
        HTTP_CLIENT = httpx.AsyncClient(timeout=60)

    t0 = time.time()
    try:
        resp = await HTTP_CLIENT.post(LMSTUDIO_API, json=payload)
        resp.raise_for_status()
        data = resp.json()
        raw_response = data["choices"][0]["message"]["content"]
        print(f"  [ask_model] main LLM call: {time.time() - t0:.2f}s")
        print(f"  [ask_model] TOTAL: {time.time() - t_total:.2f}s")
        return clean_response(raw_response)
    except httpx.HTTPStatusError:
        return "⚠️ Люми не видит локальную модель. Запусти LM Studio."
    except Exception:
        return "⚠️ Ошибка локальной модели."


async def cleanup_http():
    global HTTP_CLIENT
    if HTTP_CLIENT is not None:
        await HTTP_CLIENT.aclose()
