# Lumi Userbot

A Telegram **userbot** integrated with a local LLM (LM Studio).  
Responds to messages, remembers chat history, and speaks in different moods. Triggered by the name **“Lumi”**.
![Lumi Image]([example.png](https://github.com/SkillichSE/Lumi-userbot/blob/main/Lumi.png)
---

## Features

- Local AI replies via LM Studio (`llama-3.1-8b-instruct`) 
- Chat memory per conversation  
- Multiple moods (friendly, sarcastic, formal, funny, aggressive, horny, uncensored, shy)  
- Commands for memory and bot management  
- Owner-only reset command  

---

## Installation

1. **Clone the repo:**  
```bash
git clone <repo_url>
cd lumi-userbot
```

2. **Create a virtual environment and install dependencies:**  
```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
```

3. **Copy `.env.example` to `.env` and fill in your data:**  
```env
TG_API_ID=12345678
TG_API_HASH="1234567890"
OWNER_ID=1212121212
SESSION_NAME="lumi_userbot"
```

4. **Run the bot:**  
```bash
python start_work.py
```

> Make sure **LM Studio** is running at `http://localhost:1234`.

---

## Commands

**General:**

- `/lumi` — info and project links  
- `/commands` — command reference  
- `/ping` — check response time  
- `/model` — show active model  
- `/prompt` — show system prompt  

**Memory:**

- `/memorize <text>` — save a note  
- `/show_memory` — list saved notes  
- `/forget` — delete all notes  
- `/forget <number>` — delete a single note  

**Moods:**

- `/mood` — show current mood  
- `/mood <mood>` — set mood (friendly, sarcastic, formal, funny, aggressive, horny, uncensored, shy)  
- `/mood list` — list available moods  

**Owner-only (OWNER_ID):**

- `/reset` — clear chat memory, history, and reset mood  

---

## LM Studio Settings

- Default API: `http://localhost:1234/v1/chat/completions`  
- Default model: `llama-3.1-8b-instruct`  
- Request timeout: 60s  

---

## Notes

- User-facing messages: **Russian**  
- Developer comments, README, and instructions: **English**  
- `PROJECT_LINKS` in code can be changed for your own references  


