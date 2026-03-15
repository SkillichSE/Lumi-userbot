import json
from pathlib import Path

from config import DATA_DIR


def get_chat_file(prefix, chat_id):
    path = Path(DATA_DIR) / f"{prefix}_{chat_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
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
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_memory_text(chat_id):
    try:
        mem = load_chat_data("memory", chat_id).get("notes", [])
        if not mem:
            return ""
        return "\n".join(f"- {x}" for x in mem)
    except Exception:
        return ""
