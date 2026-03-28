from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


class SchedulerService:

    def __init__(self, bot, match_service, users_repository, favorites_repository):
        self.bot = bot
        self.match_service = match_service
        self.users_repository = users_repository
        self.favorites_repository = favorites_repository
        self.scheduler = AsyncIOScheduler()

    def start(self):
        # Daily summary every day at 09:00
        self.scheduler.add_job(
            self.daily_summary,
            CronTrigger(hour=9, minute=0)
        )

        # Check reminders every minute
        self.scheduler.add_job(
            self.check_reminders,
            "interval",
            minutes=1
        )

        self.scheduler.start()

    # ============================
    # DAILY SUMMARY
    # ============================

    async def daily_summary(self):
        users = self.users_repository.get_all()

        for user_id in users:
            timezone, daily_enabled, _ = self.users_repository.get_settings(user_id)

            if not daily_enabled:
                continue

            tz = ZoneInfo(timezone)
            today = datetime.now(tz).strftime("%Y-%m-%d")

            fixtures = await self.match_service.api_client.get_fixtures_by_date(today)

            if not fixtures:
                continue

            text = "⚽ Today's Matches\n\n"

            for match in fixtures[:5]:
                home = match["teams"]["home"]["name"]
                away = match["teams"]["away"]["name"]
                league = match["league"]["name"]
                date = match["fixture"]["date"][:16].replace("T", " ")

                text += f"{home} vs {away}\n{league}\n{date}\n\n"

            try:
                await self.bot.send_message(user_id, text)
            except Exception:
                continue

    # ============================
    # REMINDERS
    # ============================

    async def check_reminders(self):
        users = self.users_repository.get_all()

        for user_id in users:
            timezone, _, reminders_enabled = self.users_repository.get_settings(user_id)

            if not reminders_enabled:
                continue

            tz = ZoneInfo(timezone)
            now = datetime.now(tz)

            favorites = self.favorites_repository.get(user_id)

            for team_name in favorites:
                teams = await self.match_service.search_team(team_name)
                if not teams:
                    continue

                team_id = teams[0]["team"]["id"]

                fixtures = await self.match_service.get_team_matches(team_id)
                if not fixtures:
                    continue

                match = fixtures[0]

                match_time_str = match["fixture"]["date"]
                match_time = datetime.fromisoformat(match_time_str.replace("Z", "+00:00"))
                match_time = match_time.astimezone(tz)

                if timedelta(minutes=25) <= (match_time - now) <= timedelta(minutes=35):

                    home = match["teams"]["home"]["name"]
                    away = match["teams"]["away"]["name"]

                    text = (
                        f"⏰ Match Reminder\n\n"
                        f"{home} vs {away}\n"
                        f"Starts at {match_time.strftime('%H:%M')}\n\n"
                        f"Don't miss it!"
                    )

                    try:
                        await self.bot.send_message(user_id, text)
                    except Exception:
                        continue