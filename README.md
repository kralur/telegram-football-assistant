# ⚽ Telegram Football Assistant Bot

A Telegram bot that provides football fixtures, league standings, and personalized features using external sports data APIs.

---

## 🚀 Features

- ⚽ View football matches:
  - Today
  - By specific date
  - For favorite teams
- 🏆 League standings (Top 5 teams)
- ⭐ Favorite teams (saved per user)
- 🧭 Interactive inline keyboard (Telegram UI)
- 💾 SQLite database for persistent user data
- 🛡 Graceful handling of empty API responses

---

## 🧱 Architecture

The project follows a layered architecture:

- `bot/` – Telegram bot logic and handlers
- `services/` – External API integrations (API-Football)
- `db/` – SQLite database logic
- `config/` – Environment configuration
- `.env` – API keys and secrets


---

## ⚙️ Tech Stack

- Python 3.11+
- aiogram
- SQLite
- API-Football
- python-dotenv

---

## ▶️ How to Run

1. Clone the repository:
```bash
git clone https://github.com/kralur/telegram-football-assistant.git
cd telegram-football-assistant

2. Create virtual environment:
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

3. Install dependencies:
pip install -r requirements.txt

4. Create .env file:
TELEGRAM_BOT_TOKEN=8278692462:AAEMR1-Nw5VFgpotzDzTGS6qUGS1xoGrdXA
FOOTBALL_API_KEY=8f5493409b6b1cfe172c12823b61589a

5. Run the bot:
python -m src.bot.main



🤖 Bot Commands & Buttons
/start – Start the bot
/date YYYY-MM-DD – Matches by date
/fav TEAM_NAME – Add team to favorites


Buttons:
⚽ Matches today
📅 Matches by date
🏆 League standings
⭐ Favorite teams
⭐ Favorite matches


🎓 Academic Purpose
This project was developed as a capstone project and demonstrates:
External API integration
Database persistence
Event-driven architecture
Error handling and validation
User-centered design via Telegram interface


📌 Author
Umid Kuchkarbayev
