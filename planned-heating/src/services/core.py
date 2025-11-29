from adapter import event_generator
import adapter.churchtools
from adapter.tado import TadoAdapter
from adapter.tadocache import CachingTadoAdapter
from adapter.ical_retriever import ICalRetriever
from adapter.event_generator import EventGenerator
import asyncio
from datetime import date, datetime, time, timedelta
from functools import reduce
import logging, logging.handlers
from models.events import AllCalendarEvents
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

        all_events = AllCalendarEvents()

        if self.settings.schedules:
            all_events = \
                EventGenerator(self.settings.schedules) \
                    .generate_events(from_date, to_date)

        having_updates = False

        # retrieve events from iCal calendars
        if self.settings.ical_calendars:
            all_calendar_events, calendars_having_updates = \
                ICalRetriever(self.settings.ical_calendars) \
                    .retrieve_events(from_date, to_date)
            if calendars_having_updates:
                having_updates = calendars_having_updates
            all_events.events.update(all_calendar_events.events)

        # retrieve bookings from ChurchTools resources
        if self.settings.churchtools and self.settings.churchtools.url:
            all_resources_events, resources_having_updates = \
                adapter.churchtools.ResourceBookingsRetriever(self.settings.churchtools) \
                    .retrieve_events_of_all_resources(assigned_resource_names, from_date, to_date)
            if calendars_having_updates:
                having_updates = calendars_having_updates
            all_events.events.update(all_resources_events.events)

        if message.full_update:
            self.logger.info('Performing a full update of all Tado zones.')
        elif message.config_changed:
            self.logger.info('Configuration changed. Performing a full update of all Tado zones.')
        elif having_updates:
            # are there any required resources having updates? (set intersection)
            zones_outdated = set([a.tadozone for a in self.settings.assignments if set(a.calendar_names) & calendars_having_updates])
            if zones_outdated:
                self.logger.debug('Tado zones that need to be updated due to Calendar updates: %s', zones_outdated)
            else:
                self.logger.info('No Calendar has relevant updates. All Tado zones are up to date.')
                return
        else:
            self.logger.info('No Calendar has updates. All Tado zones are up to date.')

        # generate weekly schedules for all zones
        tado = CachingTadoAdapter(self.tado, message.full_update)
        home_schedules = self.generate_schedules_for_all_zones(all_events, from_date, tado)
        self.logger.debug('Updated set of schedules: %s', home_schedules)
        tado.set_schedules_for_all_zones(home_schedules)


    def generate_schedules_for_all_zones(self, all_resources_events: AllCalendarEvents, from_date: date, tado: TadoAdapter) -> HomeSchedules:

        home_schedules = HomeSchedules()
        for a in self.settings.assignments:

            # select events from required resources
            events = all_resources_events.select_events(a.calendar_names)
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

