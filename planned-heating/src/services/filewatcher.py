import asyncio
import logging, logging.handlers
import os

from services.core import Message

class Service:
    logger: logging.Logger = logging.getLogger(__name__)
    file_path: str
    queue: asyncio.Queue
    interval: float
    
    def __init__(self, file_path: str, queue: asyncio.Queue, interval: float = 1):
        self.file_path = file_path
        self.queue = queue
        self.interval = interval

    async def run(self):
        try:
            last_modified = os.path.getmtime(self.file_path)
        except Exception as e:
            last_modified = None
            self.logger.exception('Failed getting modified timestamp of file "%s": %s', self.file_path, e)
            
        try:
            while True:
                try:
                    current_modified = os.path.getmtime(self.file_path)
                    if not last_modified or current_modified != last_modified:
                        self.logger.debug('File "%s" has changed. Submitting work. Payload: %s', self.file_path, self.message)
                        self.queue.put_nowait(Message(config_changed = True))

                        last_modified = current_modified
                
                except Exception as e:
                    self.logger.exception('Failed getting modified timestamp of file "%s": %s', self.file_path, e)

                await asyncio.sleep(self.interval)

        except asyncio.CancelledError:
            pass
