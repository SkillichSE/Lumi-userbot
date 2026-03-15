from config import HISTORY_MAX

LUMI_HISTORY = {}


def add_to_history(chat_id, username, message_text, is_bot=False):
    if chat_id not in LUMI_HISTORY:
        LUMI_HISTORY[chat_id] = []
    LUMI_HISTORY[chat_id].append((username, message_text, is_bot))
    LUMI_HISTORY[chat_id] = LUMI_HISTORY[chat_id][-HISTORY_MAX:]


def get_last_messages_text(chat_id):
    chat_history = LUMI_HISTORY.get(chat_id, [])
    lines = []
    for username, msg, is_bot in chat_history[-HISTORY_MAX:]:
        prefix = "Люми" if is_bot else username
        lines.append(f"{prefix}: {msg}")
    return "\n".join(lines)
