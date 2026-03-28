import logging
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo


class NotifyService:
    def __init__(
        self,
        notification_repo,
        reminder_log_repo,
        favorites_service,
        match_service,
        users_repository,
        bot,
    ):
        self.notification_repo = notification_repo
        self.reminder_log_repo = reminder_log_repo
        self.favorites_service = favorites_service
        self.match_service = match_service
        self.users_repository = users_repository
        self.bot = bot
        self.logger = logging.getLogger("football_bot")

    async def subscribe(self, user_id: int, match_id: int):
        match = await self.match_service.get_match(match_id)
        if not match or not match.get("date"):
            return None

        kickoff = self._parse_datetime(match["date"])
        if kickoff <= datetime.now(UTC):
            return None

        notify_time = kickoff - timedelta(minutes=15)
        self.notification_repo.upsert_notification(
            user_id=user_id,
            match_id=match_id,
            notify_time=notify_time.isoformat(),
        )
        self.logger.info("Notification scheduled for user=%s match=%s", user_id, match_id)
        return match

    async def sync_favorites_for_user(self, user_id: int):
        favorites = self.favorites_service.get_user_favorites(user_id)
        for favorite in favorites:
            team_id = favorite.get("team_id")
            if team_id is None:
                raw_results = await self.match_service.search_team(favorite["team_name"])
                if not raw_results:
                    continue
                team_id = raw_results[0].get("team", {}).get("id")
                if team_id is None:
                    continue
                self.favorites_service.add_team(
                    user_id=user_id,
                    team_name=favorite["team_name"],
                    team_id=team_id,
                )

            matches = await self.match_service.get_team_matches(team_id, limit=1)
            if not matches:
                continue

            next_match = matches[0]
            if next_match.get("id") is None:
                continue

            await self.subscribe(user_id, next_match["id"])

    async def process_notifications(self):
        now = datetime.now(UTC).isoformat()
        due_notifications = self.notification_repo.get_due_notifications(now)

        for notification in due_notifications:
            user_id = notification["user_id"]
            match_id = notification["match_id"]

            if self.reminder_log_repo.has_record(user_id, match_id):
                self.notification_repo.mark_sent(notification["id"])
                continue

            match = await self.match_service.get_match(match_id)
            if not match:
                continue

            try:
                timezone = self.users_repository.get_timezone(user_id)
                await self.bot.send_message(user_id, self._build_notification_text(match, timezone))
                self.notification_repo.mark_sent(notification["id"])
                self.reminder_log_repo.add_record(
                    user_id=user_id,
                    fixture_id=match_id,
                    sent_at=datetime.now(UTC).isoformat(),
                )
                self.logger.info("Notification sent for user=%s match=%s", user_id, match_id)
            except Exception as exc:
                self.logger.exception(
                    "Failed to send notification for user=%s match=%s: %s",
                    user_id,
                    match_id,
                    exc,
                )

    def list_pending_notifications(self, user_id: int):
        return self.notification_repo.list_pending_for_user(user_id)

    @staticmethod
    def _build_notification_text(match: dict, timezone: str):
        kickoff = NotifyService._format_datetime(match["date"], timezone)
        return (
            "Match reminder\n\n"
            f"{match['home']} vs {match['away']}\n"
            f"{match['league']}\n"
            f"Kickoff: {kickoff} ({timezone})"
        )

    @staticmethod
    def _format_datetime(value: str, timezone: str):
        dt = NotifyService._parse_datetime(value)
        return dt.astimezone(ZoneInfo(timezone)).strftime("%Y-%m-%d %H:%M")

    @staticmethod
    def _parse_datetime(value: str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
