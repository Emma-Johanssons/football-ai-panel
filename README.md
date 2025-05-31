# 🧠 Football AI Panel

> An AI simulation of a live football halftime panel — just like on TV.  
> But instead of experts and broadcasters, each seat is taken by a specialized AI agent.

---

## 🖼️ What is this?

Think: the classic football halftime show.

- Multiple personalities
- Different perspectives
- Heated debates, real-time analysis
- No hand-raising — everyone speaks freely

This project simulates that familiar football panel — but with AI. Each agent has its own role, voice, and perspective, offering autonomous, opinionated takes on live football events.

---

## 🧩 The AI Panelists

| Agent         | Role             | Behavior                                             |
| ------------- | ---------------- | ---------------------------------------------------- |
| `stats_agent` | Stats expert     | Focused on data: possession, xG, shots, set pieces   |
| `coach_agent` | Tactical analyst | Talks formations, subs, pressing, transitions        |
| `ref_agent`   | Referee analyst  | Gives judgment on fouls, VAR, and officiating        |
| `fan_agent`   | Supporter voice  | Emotional, biased, pub-style takes                   |
| `host_agent`  | Moderator        | Guides conversation, asks questions, switches topics |

⚠️ Agents respond independently — there is no enforced turn-taking or order. The goal is to simulate a lively, **free-flowing discussion**.

---

## 🛠️ Built With

- **FastAPI** – for serving the chat interface
- **OpenAI GPT-4o** – agent personas powered by LLMs
- **Docker** – hot-reloading dev environment
- **D-ID, ElevateLab (optional)** – planned avatar and memory extensions

---

## 🔌 Getting Started

```bash
git clone https://github.com/emma-johanssons/football-ai-panel.git
cd football-ai-panel

# set your OpenAI API key
echo "OPENAI_API_KEY=sk-..." > .env

# start with Docker
docker-compose up --build
```
