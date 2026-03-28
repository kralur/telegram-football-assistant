import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.config.settings import SCHEDULER_INTERVAL_SECONDS


class SchedulerService:
    def __init__(self, bot, match_service, users_repository, notify_service):
        self.bot = bot
        self.match_service = match_service
        self.users_repository = users_repository
        self.notify_service = notify_service
        self.scheduler = AsyncIOScheduler()
        self.logger = logging.getLogger("football_bot")

    def start(self):
        self.scheduler.add_job(
            self.sync_notifications,
            "interval",
            seconds=SCHEDULER_INTERVAL_SECONDS,
            max_instances=1,
        )
        self.scheduler.add_job(
            self.daily_summary,
            CronTrigger(hour=9, minute=0),
            max_instances=1,
        )
        self.scheduler.start()

    async def sync_notifications(self):
        try:
            for user_id in self.users_repository.get_all():
                _, _, reminders_enabled = self.users_repository.get_settings(user_id)
                if not reminders_enabled:
                    continue
                await self.notify_service.sync_favorites_for_user(user_id)

            await self.notify_service.process_notifications()
        except Exception as exc:
            self.logger.exception("Scheduler sync failed: %s", exc)

    async def daily_summary(self):
        try:
            matches = await self.match_service.get_today_matches()
            if not matches:
                return

            for user_id in self.users_repository.get_all():
                timezone, daily_enabled, _ = self.users_repository.get_settings(user_id)
                if not daily_enabled:
                    continue
                try:
                    summary = self._build_daily_summary(matches, timezone)
                    await self.bot.send_message(user_id, summary)
                except Exception as exc:
                    self.logger.exception(
                        "Failed to send daily summary to user=%s timezone=%s: %s",
                        user_id,
                        timezone,
                        exc,
                    )
        except Exception as exc:
            self.logger.exception("Daily summary failed: %s", exc)

    @staticmethod
    def _build_daily_summary(matches: list[dict], timezone: str):
        lines = [f"Today's matches ({timezone})", ""]
        zone = ZoneInfo(timezone)
        for match in matches[:5]:
            lines.append(f"{match['home']} vs {match['away']}")
            lines.append(match["league"])
            lines.append(
                datetime.fromisoformat(match["date"].replace("Z", "+00:00"))
                .astimezone(zone)
                .strftime("%Y-%m-%d %H:%M")
            )
            lines.append("")
        return "\n".join(lines).strip()
