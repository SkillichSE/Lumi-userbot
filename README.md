<div align="center">
  <img width="600" height="600" alt="Lumi Bot" src="https://github.com/user-attachments/assets/15d9ccbb-9cee-4afd-ba67-eebfe8ee168d" />
  
  # Lumi Userbot
  
  **Telegram userbot integrated with local LLM (LM Studio)**
  
  Responds to messages, remembers chat history, and speaks in different moods. Triggered by the name **"Lumi"**.
  
  [![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
  [![Telethon](https://img.shields.io/badge/Telethon-1.24+-2CA5E0?style=flat-square&logo=telegram&logoColor=white)](https://docs.telethon.dev)
  [![LM Studio](https://img.shields.io/badge/LM_Studio-Local_AI-FF6B6B?style=flat-square)](https://lmstudio.ai)
  
  **User-facing messages: Russian**
  
</div>

---

## Features

<table>
<tr>
<td width="50%">

**Local AI Integration**
- LM Studio API (`llama-3.1-8b-instruct`)
- Automatic web search via DuckDuckGo

</td>
<td width="50%">

**Smart Memory System**
- Per-chat conversation history
- Persistent memory notes stored in `data/`
- Contextual responses

</td>
</tr>
<tr>
<td>

**Multiple Personalities**
- friendly, sarcastic, formal, funny
- aggressive, shy, creative, philosophical, minimal, chaotic

</td>
<td>

**Management Commands**
- Memory operations
- Mood switching
- Owner-only controls

</td>
</tr>
</table>

<details>
<summary style="font-size: 56px; font-weight: bold;">📸 View Screenshots</summary>

### Chat Example
<img width="990" alt="Chat" src="https://github.com/user-attachments/assets/3ce9da92-3388-44bb-8b5f-8f02a46e442b" />

### Memory System
<img width="392" alt="Memory" src="https://github.com/user-attachments/assets/527b42fd-9e24-4ac4-a409-45efddb6a001" />

### Mood Selection
<img width="702" alt="Moods" src="https://github.com/user-attachments/assets/50d58138-2dd3-4f41-bca5-149a9e72b2b8" />

### Commands
<img width="624" alt="Commands" src="https://github.com/user-attachments/assets/f47ec303-9323-4f10-9791-eea932d35ea1" />

### Reset Function
<img width="588" alt="Reset" src="https://github.com/user-attachments/assets/8185d2ef-34f4-47c9-aacd-80217a697187" />

</details>

---

## Installation
```bash
# Clone repository
git clone <repo_url>
cd lumi-bot

# Setup virtual environment
python -m venv .venv

# Activate environment
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Copy `.env.example` to `.env` and configure:
```env
TG_API_ID=12345678
TG_API_HASH=your_api_hash
OWNER_IDS=123456789,987654321
SESSION_NAME=lumi_userbot
```

### Running
```bash
python main.py
```

> **Important:** LM Studio must be running at `http://localhost:1234`

---

## Project Structure

```
lumi/
├── main.py           # entry point
├── config.py         # all constants and env variables
├── requirements.txt
├── .env.example
├── ai/
│   ├── model.py      # ask_model, clean_response
│   ├── moods.py      # mood prompts
│   └── search.py     # classifier, DuckDuckGo, analyze_and_search
├── bot/
│   ├── handler.py    # message handler, rate limiting
│   ├── commands.py   # all /commands
│   └── console.py    # console debug mode
└── utils/
    ├── storage.py    # chat data persistence (saved to data/)
    └── history.py    # in-memory conversation history
```

---

## Commands Reference

### General
| Command | Description |
|---------|-------------|
| `/ping` | Check response time |
| `/model` | Show active model |
| `/prompt` | Show current system prompt |

### Memory Management
| Command | Description |
|---------|-------------|
| `/memorize <text>` | Save a note |
| `/show_memory` | List saved notes |
| `/forget` | Delete all notes |
| `/forget <number>` | Delete specific note |

### Mood Control
| Command | Description |
|---------|-------------|
| `/mood` | Show current mood |
| `/mood <mood>` | Set mood |
| `/mood list` | List available moods |

**Available moods:** `sarcastic`, `friendly`, `formal`, `funny`, `aggressive`, `shy`, `creative`, `philosophical`, `minimal`, `chaotic`

### Owner Commands
| Command | Description |
|---------|-------------|
| `/reset` | Clear history, memory and reset mood |
| `/set_prompt <text>` | Override system prompt for current chat |

---

## LM Studio Configuration
```yaml
API Endpoint: http://localhost:1234/v1/chat/completions
Default Model: llama-3.1-8b-instruct
Request Timeout: 60 seconds
Temperature: 0.5
Max Tokens: 200
```

---

## Technical Notes

- **User-facing messages:** Russian
- **Developer resources:** English
- **History size:** Configurable via `HISTORY_MAX` in `config.py`
- **Memory files:** Stored in `data/` directory, excluded from git
- **PROJECT_LINKS:** Customizable in `config.py`

---

<div align="center">

**Made with local AI**

</div>
