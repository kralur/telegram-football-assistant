from dataclasses import dataclass
from logging import Logger

from src.config.settings import OPENAI_API_KEY
from src.core.logger import setup_logger
from src.db.database import init_db
from src.db.repositories.favorites_repository import FavoritesRepository
from src.db.repositories.notification_repository import NotificationRepository
from src.db.repositories.reminder_log_repository import ReminderLogRepository
from src.db.repositories.users_repository import UsersRepository
from src.infrastructure.cache import TTLCache
from src.infrastructure.football_api_client import FootballApiClient
from src.infrastructure.openai_client import OpenAIClient
from src.services.analysis_service import AnalysisService
from src.services.favorites_service import FavoritesService
from src.services.match_service import MatchService
from src.services.notify_service import NotifyService
from src.services.scheduler_service import SchedulerService
from src.services.search_service import SearchService


@dataclass
class ServiceContainer:
    logger: Logger
    cache: TTLCache
    football_client: FootballApiClient
    openai_client: OpenAIClient | None
    users_repository: UsersRepository
    favorites_repository: FavoritesRepository
    notification_repository: NotificationRepository
    reminder_log_repository: ReminderLogRepository
    match_service: MatchService
    analysis_service: AnalysisService | None
    favorites_service: FavoritesService
    search_service: SearchService

    async def aclose(self):
        await self.football_client.aclose()
        if self.openai_client is not None:
            await self.openai_client.client.aclose()


def build_service_container(include_analysis: bool = True) -> ServiceContainer:
    logger = setup_logger()
    init_db()

    cache = TTLCache()
    football_client = FootballApiClient()

    users_repository = UsersRepository()
    favorites_repository = FavoritesRepository()
    notification_repository = NotificationRepository()
    reminder_log_repository = ReminderLogRepository()

    match_service = MatchService(football_client, cache)

    openai_client = None
    analysis_service = None
    if include_analysis and OPENAI_API_KEY:
        openai_client = OpenAIClient()
        analysis_service = AnalysisService(openai_client, cache)

    favorites_service = FavoritesService(favorites_repository, match_service)
    search_service = SearchService(match_service, cache)

    return ServiceContainer(
        logger=logger,
        cache=cache,
        football_client=football_client,
        openai_client=openai_client,
        users_repository=users_repository,
        favorites_repository=favorites_repository,
        notification_repository=notification_repository,
        reminder_log_repository=reminder_log_repository,
        match_service=match_service,
        analysis_service=analysis_service,
        favorites_service=favorites_service,
        search_service=search_service,
    )


def build_notify_service(services: ServiceContainer, bot) -> NotifyService:
    return NotifyService(
        services.notification_repository,
        services.reminder_log_repository,
        services.favorites_service,
        services.match_service,
        services.users_repository,
        bot,
    )


def build_scheduler_service(services: ServiceContainer, bot, notify_service: NotifyService) -> SchedulerService:
    return SchedulerService(
        bot=bot,
        match_service=services.match_service,
        users_repository=services.users_repository,
        notify_service=notify_service,
    )
