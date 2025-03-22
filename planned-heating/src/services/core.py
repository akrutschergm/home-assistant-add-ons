import adapter.churchtools
from adapter.tado import TadoAdapter
from adapter.tadocache import CachingTadoAdapter
import asyncio
from datetime import date, datetime, time, timedelta
import logging, logging.handlers
from models.events import AllResourcesEvents
from models.schedules import DailySchedule
from models.settings import CoreSettings
from models.tadoschedules import ZoneSchedules, HomeSchedules
import time


class Message:
    config_changed: bool = False
    full_update: bool = False

    def __init__(self, config_changed: bool = False, full_update: bool = False):
        self.config_changed = config_changed
        self.full_update = full_update


class Service:
    logger: logging.Logger = logging.getLogger(__name__)
    config_file: str
    queue: asyncio.Queue
    tado: TadoAdapter

    def __init__(self, config_file: str, queue: asyncio.Queue, tado: TadoAdapter):
        self.config_file = config_file
        self.queue = queue
        self.tado = tado

    async def run(self):
        try:
            while True:
                # Get a "work item" out of the queue.
                msg = await self.queue.get()

                # Wait until the queue is fully processed.
                started_at = time.monotonic()
                try:
                    config = CoreSettings.load_from(self.config_file)

                    self.logger.debug('Starting work, message: %s', msg)
                    Worker(config, self.tado).execute(msg)

                    duration = time.monotonic() - started_at
                    self.logger.debug('Finished work after %.2f seconds', duration)

                except Exception as e:
                    duration = time.monotonic() - started_at
                    self.logger.exception('Failed work after %.2f seconds with: %s', duration, e)

                # Notify the queue that the "work item" has been processed.
                self.queue.task_done()

        except asyncio.CancelledError:
            pass


class Worker:
    logger: logging.Logger = logging.getLogger(__name__)
    settings: CoreSettings
    tado: TadoAdapter

    def __init__(self, settings: CoreSettings, tado: TadoAdapter):
        self.settings = settings
        self.tado = tado

    def execute(self, message: Message):

        from_date = datetime.now().date()
        to_date = from_date + timedelta(days=6)

        assigned_resource_names = set[str]
        for a in self.settings.assignments:
            assigned_resource_names = assigned_resource_names.union(set(a.resources))

        ct = adapter.churchtools.ResourceBookingsRetriever(self.settings.churchtools)
        all_resources_events, resources_having_updates = \
            ct.retrieve_events_of_all_resources(assigned_resource_names, from_date, to_date)

        if resources_having_updates:
            self.logger.info('ChurchTools Resources having updates: %s', resources_having_updates)
        else:
            self.logger.info('ChurchTools Resources do not have updates')

        # are there any required resources having updates? (set intersection)
        zones_outdated = set([a.tadozone for a in self.settings.assignments if set(a.resources) & resources_having_updates])
        if not message.full_update and not message.config_changed and not zones_outdated:
            if resources_having_updates:
                self.logger.info('All Tado zones are up to date.')
            return

        if zones_outdated:
            self.logger.debug('Tado zones that need to be updated due to changed events: %s', zones_outdated)

        # generate weekly schedules for all zones
        tado = CachingTadoAdapter(self.tado, message.full_update)
        home_schedules = self.generate_schedules_for_all_zones(all_resources_events, from_date, tado)
        tado.set_schedules_for_all_zones(home_schedules)


    def generate_schedules_for_all_zones(self, all_resources_events: AllResourcesEvents, from_date: date, tado: TadoAdapter) -> HomeSchedules:

        home_schedules = HomeSchedules()
        for a in self.settings.assignments:

            # select events from required resources
            events = all_resources_events.select_events(a.resources)
            warm = a.warm or self.settings.heating.warm
            cold = a.cold or self.settings.heating.cold
            earlystart = a.earlystart or self.settings.heating.earlystart

            # calculate time schedule for each day of the week
            # list of schedules in order of the weekday where the index is 0=monday to 6=sunday
            schedules = list([None for _ in range(0, 7)])
            for d in [from_date + timedelta(days = n) for n in range(0, 7)]: # iterate days starting with from_date. n is NOT the weekday
                schedules[d.weekday()] = DailySchedule.from_events(d, events, warm, cold, earlystart)

            home_schedules.insert(ZoneSchedules(name = a.tadozone,
                                                id = tado.get_zone_id(a.tadozone),
                                                daily_schedules = schedules))
        return home_schedules

