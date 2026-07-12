from datetime import UTC, datetime

from application.interfaces.clock import IClock


class SystemClock(IClock):
    def now(self) -> datetime:
        return datetime.now(UTC)
