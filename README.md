# InterviewCoach AI 🎙️

An AI-powered interview preparation app built with Streamlit.  
Practice voice answers → get transcribed → scored locally → reviewed by AI.

---

## Features
- **Practice Page** — Record voice answers, get transcribed via Groq Whisper, scored locally, then AI feedback via OpenRouter
- **Question Bank** — Generate 15 personalised questions with categories, difficulty, and why-asked explanations
- **Coding Round** — AI-generated coding problems with a code editor, test runner, and full AI code review
- **Dashboard** — Progress charts (score over time, by category, filler words), session history

## Tech Stack
| Layer | Tool |
|-------|------|
| UI | Streamlit |
| Auth | bcrypt (local JSON files) |
| Transcription | Groq Whisper (whisper-large-v3-turbo) |
| LLM | OpenRouter (Llama 3.3 70B, free tier) |
| Charts | Plotly |
| Storage | Local JSON files |

---

## Setup Instructions

### Step 1 — Clone / download the project
Place the project folder anywhere on your machine.

### Step 2 — Install Python
Requires Python 3.10 or higher.  
Check: `python --version`

### Step 3 — Create a virtual environment (recommended)
```bash
cd InterviewCoachAI
python -m venv venv

# Activate:
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### Step 4 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 5 — Get your FREE API keys

#### Groq API Key (for Whisper transcription)
1. Go to https://console.groq.com
2. Sign up (free, no credit card)
3. Go to API Keys → Create API Key
4. Copy the key (starts with `gsk_...`)

#### OpenRouter API Key (for LLM)
1. Go to https://openrouter.ai
2. Sign up (free)
3. Go to Keys → Create Key
4. Copy the key (starts with `sk-or-v1-...`)
5. The models used are **completely free** (Llama 3.3 70B, Mistral 7B)

### Step 6 — Add your API keys
Edit the file `.streamlit/secrets.toml`:
```toml
GROQ_API_KEY = "gsk_your_actual_key_here"
OPENROUTER_API_KEY = "sk-or-v1-your_actual_key_here"
```

### Step 7 — Run the app
```bash
streamlit run app.py
```

The app will open at: **http://localhost:8501**

---

## Project Structure
```
InterviewCoachAI/
├── app.py                          # Entry gate — auth + home
├── requirements.txt
├── .streamlit/
│   ├── config.toml                 # Theme settings
│   └── secrets.toml                # API keys (never commit!)
├── pages/
│   ├── 1_Interview_Practice.py     # Voice practice + AI feedback
│   ├── 2_Interview_Questions.py    # Question bank
│   ├── 3_Dashboard.py              # Analytics
│   └── 4_Coding_Round.py          # Coding simulator
├── utils/
│   ├── auth_utils.py               # bcrypt auth, user JSON R/W
│   ├── whisper_utils.py            # Groq Whisper transcription
│   ├── analysis_utils.py           # Local scoring (no API)
│   ├── llm_utils.py                # All 5 OpenRouter LLM calls
│   └── storage_utils.py            # Session JSON save/load
└── data/                           # Auto-created, in .gitignore
    ├── users/                      # One JSON per user
    └── sessions/                   # One JSON per session
```

---

## Usage Notes
- **No microphone?** Use the file upload fallback or type your answer manually
- **Rate limited?** The app automatically falls back to Mistral 7B if Llama 3.3 70B rate-limits
- **No database** — everything is stored in local JSON files in `data/`
- **Private** — `data/` is in `.gitignore`, so user data is never pushed to git

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` again |
| Transcription fails | Check `GROQ_API_KEY` in `secrets.toml` |
| AI feedback fails | Check `OPENROUTER_API_KEY` in `secrets.toml` |
| Mic not working | Use file upload or type answer manually |
| Port already in use | Run `streamlit run app.py --server.port 8502` |
