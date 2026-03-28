# Telegram Football Assistant Bot

Telegram bot for football fixtures, live scores, standings, top scorers, favorites, and match reminders.

This project was built as a bachelor capstone project and focuses on:
- async Telegram bot development with `aiogram`
- layered architecture
- API integration with API-Football
- SQLite persistence
- inline-first user experience
- scheduled notifications with timezone support

## Features

- Inline-first Telegram UX based on `InlineKeyboard`
- Today's matches
- Live matches
- League standings
- Top scorers
- Team search
- Favorites management
- Reminder scheduling for upcoming matches
- Timezone-aware match and notification times
- In-memory TTL cache to reduce repeated API calls
- SQLite storage for users, favorites, notifications, and reminder logs

## Current UX

The bot is designed around a single inline flow:
- `/start` opens the main menu
- all main actions are triggered through inline buttons
- screens are updated through `edit_text`
- `Back` navigation returns to the previous screen
- search is handled as a lightweight screen state without FSM conflicts

## Architecture

The project follows a layered architecture:

- `src/bot/`
  Telegram routing, inline keyboards, views, screen state, pagination
- `src/services/`
  Business logic for matches, search, favorites, notifications, scheduler
- `src/infrastructure/`
  API client and cache implementation
- `src/db/`
  SQLite initialization and repositories
- `src/core/`
  Logging and shared core utilities
- `src/config/`
  Environment and runtime settings

Dependency direction:
- handlers -> services -> repositories
- handlers do not contain business logic
- services do not depend on Telegram UI details
- repositories do not know about services

## Main Modules

### MatchService

Provides:
- `get_today_matches()`
- `get_live_matches()`
- `get_standings()`
- `get_top_scorers()`
- `get_match(match_id)`

All methods return normalized data and use cache where appropriate.

### SearchService

Provides team search with cached results and normalized output.

### FavoritesService

Provides:
- add favorite team
- remove favorite team
- list favorite teams by `user_id`

### NotifyService

Provides:
- schedule notification for a match
- synchronize upcoming match notifications for favorite teams
- send reminders 15 minutes before kickoff
- prevent duplicate sends through `notifications` and `reminder_log`

### SchedulerService

Background jobs:
- sync reminders every `30` seconds by default
- send daily summary

## Database

SQLite database file: `bot.db`

Tables:
- `users`
- `favorites`
- `notifications`
- `reminder_log`

The database is created automatically on startup.

## Tech Stack

- Python 3.11+
- aiogram 3
- API-Football
- SQLite
- APScheduler
- httpx
- python-dotenv

## Environment Variables

Create a `.env` file in the project root:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
FOOTBALL_API_KEY=your_api_football_key
OPENAI_API_KEY=optional_if_used

CACHE_TTL_MATCHES=300
CACHE_TTL_STANDINGS=900
CACHE_TTL_SCORERS=900
CACHE_TTL_SEARCH=600
SCHEDULER_INTERVAL_SECONDS=30
DEFAULT_TIMEZONE=UTC
```

Notes:
- `TELEGRAM_BOT_TOKEN` is required
- `FOOTBALL_API_KEY` is required
- do not commit real secrets to GitHub

## Installation

```bash
git clone <your-repository-url>
cd telegram-football-assistant-main
python -m venv venv
```

Windows:

```powershell
venv\Scripts\activate
pip install -r requirements.txt
```

Linux/macOS:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

## Run

Recommended run command from the project root:

```powershell
venv\Scripts\python.exe -m src.app
```

Direct execution is also supported:

```powershell
cd src
python app.py
```

## Testing

Run tests:

```powershell
venv\Scripts\python.exe -m unittest discover -s tests -v
```

Current tests cover:
- match normalization and caching
- search caching
- notification scheduling and delivery flow
- timezone-aware formatting
- pagination helper logic

## Supported User Flows

1. Open the bot with `/start`
2. Browse today's or live matches
3. Open standings or top scorers by league
4. Search for a team
5. Add the team to favorites
6. Let scheduler keep upcoming reminders in sync
7. Receive notification 15 minutes before kickoff
8. Change timezone from inline settings to view local kickoff times

## Why This Project Is Strong for Defense

This project demonstrates:
- asynchronous event-driven bot architecture
- clean separation of layers
- API integration with normalization and caching
- inline-first Telegram UX
- background scheduling
- timezone-aware notifications
- persistence and duplicate protection in SQLite

## Defense Talking Points

If asked what was technically challenging:
- implemented async scheduler for notifications
- designed inline-first UX without state conflicts
- added timezone-aware reminders
- built layered architecture from handlers to services to repositories

If asked why FSM was not used:

> I used lightweight state handling instead of FSM to keep UX predictable and avoid handler conflicts.

If asked what can be improved next:
- move cache to Redis
- add Docker deployment
- improve scalability and background job observability

## Future Improvements

- Redis cache instead of in-memory cache
- Docker support
- Railway or VPS deployment
- richer league coverage
- better match pagination and filtering
- admin or analytics panel

## Author

Umid Kuchkarbayev
