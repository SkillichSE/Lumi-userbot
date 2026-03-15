import asyncio
import re
import time
import threading

from ddgs import DDGS
from config import SEARCH_CACHE_TTL

SEARCH_CACHE = {}
SEARCH_CLASSIFIER = None
SEARCH_CLASSIFIER_LOCK = threading.Lock()

SEARCH_EXAMPLES = [
    # known people
    ("кто такой Илон Маск", True),
    ("кто такая Billie Eilish", True),
    ("кто такой Навальный", True),
    ("кто снял Интерстеллар", True),
    ("кто основал Apple", True),
    ("кто написал Войну и Мир", True),
    ("кто создал Python", True),
    ("CEO Tesla", True),
    # projects, games, movies
    ("расскажи о игре Portal", True),
    ("расскажи про группу Metallica", True),
    ("когда вышел фильм Начало", True),
    ("расскажи побольше о Minecraft", True),
    ("когда вышла GTA 5", True),
    ("состав группы BTS", True),
    ("участники группы Radiohead", True),
    ("члены группы Queen", True),
    # current events and data
    ("президент США сейчас", True),
    ("курс доллара сегодня", True),
    ("погода в Москве завтра", True),
    ("последние новости", True),
    ("сколько стоит iPhone 15", True),
    ("версия Python 3.12", True),
    ("найди информацию о NVIDIA", True),
    # unknown terms — main pattern
    ("что такое блокчейн", True),
    ("что такое квантовый компьютер", True),
    ("кто такой TheOdd1sOut", True),
    ("что за мем six seven", True),
    ("что такое мем 67", True),
    ("что значит skibidi", True),
    ("что значит rizz", True),
    ("что такое gyat", True),
    ("что такое brain rot", True),
    ("что такое sigma male", True),
    ("что такое ohio мем", True),
    ("что такое NPC мем", True),
    ("что означает based", True),
    ("что значит cope", True),
    ("что такое ratio в твиттере", True),
    ("что такое touch grass", True),
    ("что такое looksmaxxing", True),
    ("что такое darkweb", True),
    ("что такое doomer", True),
    ("что такое speedrun", True),
    ("кто такой dream youtuber", True),
    ("что такое glitch", True),
    ("расскажи про аниме death note", True),
    ("что такое манга", True),
    ("что такое twitch дроп", True),
    ("что такое стрим снайпинг", True),
    ("что такое крипта", True),
    ("что такое нфт", True),
    ("расскажи про darksouls", True),
    ("что за игра hollow knight", True),
    ("кто такие дрейк и кендрик ламар", True),
    ("что за трек donda", True),
    ("что такое drill музыка", True),
    # opinions about specific people/events
    ("что думаешь о Путине", True),
    ("что думаешь о Трампе", True),
    ("что ты думаешь о Джеффри Эпштейне", True),
    ("что случилось с Эпштейном", True),
    # small talk — no search needed
    ("привет как дела", False),
    ("привет", False),
    ("пока", False),
    ("спасибо", False),
    ("как дела у тебя", False),
    ("ты умная?", False),
    ("ты тут?", False),
    ("скучно", False),
    ("хочу поговорить", False),
    # creative requests
    ("представь что ты пират", False),
    ("придумай историю о драконе", False),
    ("напиши стихотворение", False),
    ("сочини анекдот", False),
    ("расскажи историю про ведьму", False),
    ("расскажи шутку", False),
    ("придумай имя для кота", False),
    ("напиши текст песни", False),
    # task assistance
    ("помоги написать письмо", False),
    ("переведи на английский", False),
    ("напиши код на Python", False),
    ("как решить уравнение", False),
    ("исправь текст", False),
    # school knowledge — model knows without search
    ("объясни что такое рекурсия", False),
    ("как работает фотосинтез", False),
    ("объясни теорему пифагора", False),
    ("закон джоуля ленца", False),
    ("что такое закон ома", False),
    ("что такое атом", False),
    ("объясни второй закон ньютона", False),
    ("что такое интеграл", False),
    ("что такое парабола", False),
    ("что такое синус", False),
    ("что такое молекула", False),
    ("что такое гравитация", False),
    ("что такое эволюция", False),
    ("что такое демократия", False),
    ("что такое философия", False),
    ("что такое психология", False),
    ("что такое нейрон", False),
    ("что такое метафора", False),
    ("что такое глагол", False),
    ("что такое существительное", False),
    # abstract opinions
    ("что думаешь о жизни", False),
    ("что важнее деньги или счастье", False),
    ("как провезти сахар", False),
]


def load_classifier():
    global SEARCH_CLASSIFIER
    try:
        import warnings
        import logging
        import os
        warnings.filterwarnings("ignore")
        logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
        logging.getLogger("transformers").setLevel(logging.ERROR)
        logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
        logging.getLogger("filelock").setLevel(logging.ERROR)
        os.environ["TOKENIZERS_PARALLELISM"] = "false"

        from sentence_transformers import SentenceTransformer
        import numpy as np

        print("  [classifier] loading model...", flush=True)
        t0 = time.time()
        model = SentenceTransformer(
            "paraphrase-multilingual-MiniLM-L12-v2",
            local_files_only=True,
            trust_remote_code=False,
        )

        texts = [ex[0] for ex in SEARCH_EXAMPLES]
        labels = [ex[1] for ex in SEARCH_EXAMPLES]
        embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)

        SEARCH_CLASSIFIER = {
            "model": model,
            "embeddings": embeddings,
            "labels": labels,
        }
        print(f"  [classifier] ready in {time.time() - t0:.2f}s")
    except Exception as e:
        print(f"  [classifier] failed to load: {type(e).__name__}: {e}")
        print("  [classifier] falling back to keywords")
        SEARCH_CLASSIFIER = None


def classify_needs_search(prompt):
    import numpy as np

    clf = SEARCH_CLASSIFIER
    if clf is None:
        return None, 0.0

    query_emb = clf["model"].encode([prompt], convert_to_numpy=True)[0]
    example_embs = clf["embeddings"]

    norms = np.linalg.norm(example_embs, axis=1) * np.linalg.norm(query_emb)
    norms = np.where(norms == 0, 1e-9, norms)
    sims = (example_embs @ query_emb) / norms

    k = 5
    top_k = np.argsort(sims)[-k:]
    votes = [clf["labels"][i] for i in top_k]
    weights = [sims[i] for i in top_k]

    score_true = sum(w for v, w in zip(votes, weights) if v)
    score_false = sum(w for v, w in zip(votes, weights) if not v)
    total = score_true + score_false

    needs_search = score_true > score_false
    confidence = (max(score_true, score_false) / total) if total > 0 else 0.5

    return needs_search, confidence


def _build_search_query(text):
    text = re.sub(r'\b(что такое|кто такой|кто такая|что за)\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(кто|что|где|когда|как|почему|зачем|какой|какая|какие)\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(такой|такая|такое|это|есть|был|была|было|были)\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'[?!.,;:]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def analyze_and_search_sync(prompt):
    p = prompt.lower().strip()

    t0 = time.time()
    needs_search, confidence = classify_needs_search(prompt)
    print(f"  [analyze] classifier: {time.time() - t0:.3f}s, needs_search={needs_search}, confidence={confidence:.2f}")

    words = prompt.split()
    has_proper_noun = any(
        w[0].isupper() and i > 0
        for i, w in enumerate(words)
        if len(w) > 1 and w.isalpha()
    )
    if has_proper_noun:
        print(f"  [analyze] proper noun detected, forcing search")
        needs_search = True
    elif not needs_search and confidence < 0.80:
        print(f"  [analyze] low confidence, trusting model without search")
        needs_search = False

    if needs_search is None:
        keywords = ["кто", "состав", "участники", "сейчас", "когда", "где",
                    "новост", "погода", "курс", "цена", "найди", "поищи",
                    "игра", "фильм", "книга", "сериал", "расскажи о", "расскажи про",
                    "что такое", "побольше о", "побольше про",
                    "мем", "мемы", "слово", "сленг", "что значит", "что за"]
        needs_search = any(k in p for k in keywords)

    if needs_search:
        query = _build_search_query(prompt)
        print(f"  [analyze] search query: '{query}'")
        return True, query
    return False, None


async def analyze_and_search(prompt):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, analyze_and_search_sync, prompt)


async def web_search(query):
    cache_key = query.lower().strip()
    current_time = time.time()

    if cache_key in SEARCH_CACHE:
        cached_result, timestamp = SEARCH_CACHE[cache_key]
        if current_time - timestamp < SEARCH_CACHE_TTL:
            print(f"  [search] cache hit")
            return cached_result

    t0 = time.time()
    try:
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, lambda: DDGS().text(query, max_results=3))
        print(f"  [search] DuckDuckGo: {time.time() - t0:.2f}s")

        if results:
            search_text = ""
            for i, result in enumerate(results, 1):
                search_text += f"{i}. {result.get('title', 'No title')}\n"
                search_text += f"   {result.get('body', 'No description')}\n"
                search_text += f"   Source: {result.get('href', '')}\n\n"

            SEARCH_CACHE[cache_key] = (search_text, current_time)
            return search_text
        return None
    except Exception as e:
        print(f"  [search] error after {time.time() - t0:.2f}s: {e}")
        return None
