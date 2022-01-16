import asyncio
import datetime
import random
from multiprocessing import Process
from multiprocessing import Value
from typing import Optional

from security_notifier.config import Config
from security_notifier.imap import get_events
from security_notifier.imap.detection_info import DetectionInfo, EventType


def _generate_event_list():
    """Mock event generator used for testing the email poller"""

    def random_event():
        event_type = random.choice(list(EventType))
        camera_ids = [random.randint(0, 5) for _ in range(random.randint(0, 5))]
        date_time = datetime.datetime(2022, 1, random.randint(1, 31),
                                      random.randint(0, 23), random.randint(0, 59), random.randint(0, 59))
        return DetectionInfo(event_type, camera_ids, date_time)

    num_detections = random.randint(0, 10)
    return [random_event() for _ in range(num_detections)]


class EmailPoller(Process):
    def __init__(self, running_flag: Value, polling_freq: int, event_generator=get_events):
        super().__init__()
        self.detection_queue: asyncio.Queue = asyncio.Queue()
        self.polling_freq: int = polling_freq
        self._running_flag: Value = running_flag
        self.tasks: Optional[asyncio.futures.Future] = None

        self.event_generator = event_generator

    async def get_events(self, queue):
        while bool(self._running_flag.value):
            events = self.event_generator()
            for e in events:
                await queue.put(e)
            await asyncio.sleep(self.polling_freq)

    async def handle_event(self, queue):
        while bool(self._running_flag.value):
            if queue.empty():
                await asyncio.sleep(0.5)
                continue
            event = await queue.get()
            print(event)
        queue.task_done()

    async def run_tasks(self):
        self.tasks = asyncio.gather(
            self.get_events(self.detection_queue),
            self.handle_event(self.detection_queue)
        )
        await self.tasks

    def run(self):
        asyncio.run(self.run_tasks())


class PollerManager:
    def __init__(self):
        self.poller: Optional[Process] = None
        self.sentinel = Value('i', 0)

    def start(self):
        self.sentinel.value = 1
        polling_freq = Config.instance().get("imap.polling_frequency")
        self.poller = EmailPoller(self.sentinel, polling_freq=polling_freq)
        self.poller.start()

    def stop(self):
        self.sentinel.value = 0
        self.poller.join()
