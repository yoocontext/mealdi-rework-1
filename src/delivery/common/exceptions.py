from abc import ABC
from dataclasses import dataclass

from application.common.exceptions import AppError


@dataclass(kw_only=True, slots=True)
class DeliveryError(AppError, ABC):
    """Base error for transport component failures."""
