import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
API_ID = int(os.getenv("TG_API_ID", "0"))
API_HASH = os.getenv("TG_API_HASH", "")
OWNER_ID = set(int(x) for x in os.getenv("OWNER_IDS", "").split(",") if x.strip().isdigit())
SESSION_NAME = os.getenv("SESSION_NAME", "lumi_userbot")

# LM Studio
MODEL_NAME = "llama-3.1-8b-instruct"
LMSTUDIO_API = "http://localhost:1234/v1/chat/completions"

# Project links
PROJECT_LINKS = {
    "about": "https://teletype.in/@skillich/Lumi_how_to",
    "commands": "https://teletype.in/@skillich/Commands",
    "github": "https://github.com/SkillichSE/Lumi-userbot",
    "support": "https://t.me/skillich",
    "site": "https://skillichse.github.io/lumi-site",
}

# History
HISTORY_MAX = 7

# Search cache
SEARCH_CACHE_TTL = 300

# Rate limiting
RATE_LIMIT_WINDOW = 10
RATE_LIMIT_MAX = 3

# Chats to send welcome message on startup (leave empty to disable)
WELCOME_CHATS = []

# Directory for chat memory files
DATA_DIR = "data"
