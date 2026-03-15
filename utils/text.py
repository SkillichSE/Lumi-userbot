import re


def clean_response(text: str) -> str:
    """Убирает артефакты которые модель добавляет к ответам."""
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

    # Весь ответ заглавными → нормальный регистр
    words = cleaned.split()
    if len(words) > 3 and sum(1 for w in words if w.isupper() and len(w) > 1) > len(words) * 0.5:
        cleaned = cleaned.capitalize()

    # Латинские артефакты в начале (Naturally., Sure., и т.п.)
    cleaned = re.sub(r'^[A-Za-z][A-Za-z ,!.]{0,30}[.!]\s*', '', cleaned).strip()

    # Первая буква заглавная
    if cleaned and cleaned[0].islower():
        cleaned = cleaned[0].upper() + cleaned[1:]

    return cleaned
