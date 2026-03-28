import unittest
from datetime import UTC, datetime, timedelta

from src.services.notify_service import NotifyService


class FakeNotificationRepository:
    def __init__(self):
        self.notifications = {}
        self.sent = set()

    def upsert_notification(self, user_id: int, match_id: int, notify_time: str):
        self.notifications[(user_id, match_id)] = {
            "id": len(self.notifications) + 1,
            "user_id": user_id,
            "match_id": match_id,
            "notify_time": notify_time,
            "sent": 0,
        }

    def get_due_notifications(self, now_iso: str):
        return [
            value
            for value in self.notifications.values()
            if value["notify_time"] <= now_iso and value["sent"] == 0
        ]

    def mark_sent(self, notification_id: int):
        for notification in self.notifications.values():
            if notification["id"] == notification_id:
                notification["sent"] = 1

    def list_pending_for_user(self, user_id: int):
        return [
            value
            for value in self.notifications.values()
            if value["user_id"] == user_id and value["sent"] == 0
        ]


class FakeReminderLogRepository:
    def __init__(self):
        self.records = set()

    def has_record(self, user_id: int, fixture_id: int):
        return (user_id, fixture_id) in self.records

    def add_record(self, user_id: int, fixture_id: int, sent_at: str):
        self.records.add((user_id, fixture_id))


class FakeFavoritesService:
    def __init__(self):
        self.favorites = {}

    def get_user_favorites(self, user_id: int):
        return self.favorites.get(user_id, [])

    def add_team(self, user_id: int, team_name: str, team_id: int | None = None):
        current = self.favorites.setdefault(user_id, [])
        for favorite in current:
            if favorite["team_name"] == team_name:
                favorite["team_id"] = team_id
                return
        current.append({"team_name": team_name, "team_id": team_id})


class FakeMatchService:
    def __init__(self):
        self.match = {
            "id": 55,
            "date": (datetime.now(UTC) + timedelta(minutes=30)).isoformat(),
            "home": "Arsenal",
            "away": "Chelsea",
            "league": "Premier League",
        }

    async def get_match(self, match_id: int):
        match = dict(self.match)
        match["id"] = match_id
        return match

    async def search_team(self, query: str):
        return [{"team": {"id": 99, "name": query}}]

    async def get_team_matches(self, team_id: int, limit: int = 1):
        return [dict(self.match)]


class FakeBot:
    def __init__(self):
        self.sent_messages = []

    async def send_message(self, user_id: int, text: str):
        self.sent_messages.append((user_id, text))


class FakeUsersRepository:
    def get_timezone(self, user_id: int):
        return "Asia/Tashkent"


class NotifyServiceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.notification_repo = FakeNotificationRepository()
        self.reminder_log_repo = FakeReminderLogRepository()
        self.favorites_service = FakeFavoritesService()
        self.match_service = FakeMatchService()
        self.users_repository = FakeUsersRepository()
        self.bot = FakeBot()
        self.service = NotifyService(
            self.notification_repo,
            self.reminder_log_repo,
            self.favorites_service,
            self.match_service,
            self.users_repository,
            self.bot,
        )

    async def test_subscribe_creates_notification(self):
        match = await self.service.subscribe(user_id=1, match_id=55)

        self.assertEqual(match["home"], "Arsenal")
        self.assertIn((1, 55), self.notification_repo.notifications)

    async def test_process_notifications_marks_sent_and_logs_delivery(self):
        await self.service.subscribe(user_id=1, match_id=55)

        record = self.notification_repo.notifications[(1, 55)]
        record["notify_time"] = (datetime.now(UTC) - timedelta(minutes=1)).isoformat()

        await self.service.process_notifications()

        self.assertEqual(len(self.bot.sent_messages), 1)
        self.assertIn("Asia/Tashkent", self.bot.sent_messages[0][1])
        self.assertTrue(self.reminder_log_repo.has_record(1, 55))
        self.assertEqual(record["sent"], 1)

    async def test_sync_favorites_uses_team_matches(self):
        self.favorites_service.favorites[1] = [{"team_id": 99, "team_name": "Arsenal"}]

        await self.service.sync_favorites_for_user(1)

        self.assertIn((1, 55), self.notification_repo.notifications)

    async def test_sync_favorites_persists_resolved_team_id(self):
        self.favorites_service.favorites[1] = [{"team_id": None, "team_name": "Arsenal"}]

        await self.service.sync_favorites_for_user(1)

        self.assertEqual(self.favorites_service.favorites[1][0]["team_id"], 99)


if __name__ == "__main__":
    unittest.main()
