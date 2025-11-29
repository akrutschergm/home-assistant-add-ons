import asyncio
from datetime import datetime, timedelta
import logging, logging.handlers
from services.core import Message

class Service:
    logger: logging.Logger = logging.getLogger(__name__)
    minutes: float
    queue: asyncio.Queue

    def __init__(self, minutes: float, queue: asyncio.Queue):
        self.minutes = minutes
        self.queue = queue

    async def run(self):
        def get_delay(seconds: float) -> tuple[datetime, float]:
            dt = datetime.now() + timedelta(seconds= seconds)
            return (dt, seconds)

        def get_delay_to_next_full_minutes() -> tuple[datetime, float]:
            now = datetime.now()
            dt = round_minutes(now + timedelta(minutes = self.minutes), self.minutes)
            delay = (dt - now).total_seconds()
            return (dt, delay)

        def round_minutes(dt: datetime, minutes: float) -> datetime:
            return datetime(dt.year, dt.month, dt.day, dt.hour, (dt.minute // minutes) * minutes)

        try:
            dt, delay = get_delay(10)
            first_run = True

            while True:
                self.logger.debug("Waiting until %s", dt)
                await asyncio.sleep(delay)

                message = Message(full_update = first_run)
                self.logger.debug('Submitting work. Message: %s', message)
                self.queue.put_nowait(message)

                dt, delay = get_delay_to_next_full_minutes()
                first_run = False

        except asyncio.CancelledError:
            pass
