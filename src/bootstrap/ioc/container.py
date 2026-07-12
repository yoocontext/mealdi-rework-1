from dishka import AsyncContainer, make_async_container

from bootstrap.ioc.providers.delivery import DeliveryProvider
from bootstrap.ioc.providers.infra import InfraProvider
from bootstrap.ioc.providers.settings import SettingsProvider
from bootstrap.ioc.providers.use_cases import UseCaseProvider
from bootstrap.settings import Settings


def create_container(*, settings: Settings) -> AsyncContainer:
    return make_async_container(
        SettingsProvider(settings=settings),
        InfraProvider(),
        UseCaseProvider(),
        DeliveryProvider(),
    )
