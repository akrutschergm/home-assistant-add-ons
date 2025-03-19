import asyncio
from datetime import datetime, timedelta
import logging, logging.handlers
from services.core import Message

class Service:
    logger: logging.Logger = logging.getLogger(__name__)
    minutes: float
    queue: asyncio.Queue
    message: Message
    
    def __init__(self, minutes: float, queue: asyncio.Queue, message: Message):
        self.minutes = minutes
        self.queue = queue
        self.message = message

    async def run(self):
        def get_delay_to_next_full_minutes() -> tuple[datetime, float]:
            now = datetime.now()
            dt = now + timedelta(minutes = self.minutes)
            dt = datetime(dt.year, dt.month, dt.day, dt.hour, (dt.minute // self.minutes) * self.minutes)
            delay = (dt - now).total_seconds()
            return (dt, delay)

        try:
            while True:
                dt, delay = get_delay_to_next_full_minutes()
                self.logger.debug("Waiting until %s", dt)
                await asyncio.sleep(delay)
                
                self.logger.debug('Submitting work. Message: %s', self.message)
                self.queue.put_nowait(self.message)

        except asyncio.CancelledError:
            pass
