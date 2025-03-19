from churchtools import ChurchTools # https://pypi.org/project/churchtools/
from churchtools.models.resource import Booking
from datetime import date, datetime
from dateutil import tz
import json
import logging, logging.handlers
from models.events import AllResourcesEvents, Event, ResourceEvents
from models.settings import ChurchToolsSettings
import os
from typing import Optional


class ResourceBookingsRetriever:
    logger: logging.Logger = logging.getLogger(__name__)
    settings: ChurchToolsSettings
    ct: ChurchTools = None
    cached_resources: Optional[list[any]] = None

    def __init__(self, settings: ChurchToolsSettings):
        self.settings = settings

        self.ct = ChurchTools(settings.url)
        self.ct.login(settings.username, settings.password)
        self.logger.debug('Connected to ChurchTools: %s', self.ct)


    def retrieve_events_of_all_resources(self, resource_names: set[str], from_date: date, to_date: date) -> tuple[AllResourcesEvents, set[str]]:

        def utc_to_local(dt: datetime) -> datetime:
            return dt.astimezone(tz.tzlocal())

        def read_booking(b: Booking) -> Event:
            return Event(
                begin = utc_to_local(b.calculated.startDate),
                end = utc_to_local(b.calculated.endDate),
                name = b.caption)

        resource_names_and_ids = self.get_resource_ids(resource_names)
        bookings_by_resource_name = self.get_bookings_by_resource_name(resource_names_and_ids, from_date, to_date)

        all_resources_events = AllResourcesEvents()
        for resource_name, bookings in sorted(bookings_by_resource_name.items()):
            all_resources_events.resource_events[resource_name] = \
                ResourceEvents(name = resource_name,
                               id = resource_names_and_ids[resource_name],
                               events = list([read_booking(b) for b in bookings]))
        self.logger.debug('calendar events of all used resources: %s', all_resources_events)

        # determine resources that have changed events
        resources_having_updates = self.determine_resources_having_updates(all_resources_events)
        self.logger.debug('Changed resource events: %s', resources_having_updates if resources_having_updates else None)

        self.write_all_resources_events_to_cache(all_resources_events)

        return (all_resources_events, resources_having_updates)


    def get_resource_ids(self, resource_names: list[str]) -> dict[str: int]:

        # query ChurchTools for resources
        if not self.cached_resources:
            self.logger.debug('Getting resources from masterdata')
            _, self.cached_resources = self.ct.resources.masterdata()

        resource_names_and_ids = {}
        for name in resource_names:
            resource_id = next((r.id for r in self.cached_resources if r.name == name), None)
            if not resource_id:
                raise ValueError(f'Resource with name "{name}" not found in ChurchTools.')
            resource_names_and_ids[name] = resource_id

        self.logger.debug('resources: %s', resource_names_and_ids)
        return resource_names_and_ids


    def get_bookings_by_resource_name(self, resource_names_and_ids: dict[str: int], date_from: date, date_to: date) -> dict[str: list[Booking]]:

        self.logger.debug('Getting bookings for resources: %s', resource_names_and_ids)

        resource_ids = list(sorted(resource_names_and_ids.values()))
        bookings = self.ct.resources.bookings(resource_ids, status_ids = [1, 2], from_ = date_from, to = date_to)

        bookings_by_name = {}
        for name, id in resource_names_and_ids.items():
            selected_bookings = list([b for b in bookings if b.resource.id == id])
            bookings_by_name[name] = selected_bookings

        return bookings_by_name


    def determine_resources_having_updates(self, all_resources_events: AllResourcesEvents) -> set[str]:
        all_resources_events_from_cache = self.read_all_resources_events_from_cache()

        changed_resources = set()
        for resource_name in all_resources_events.resource_events:
            if (resource_name not in all_resources_events_from_cache.resource_events or
                all_resources_events.resource_events[resource_name] != all_resources_events_from_cache.resource_events[resource_name]):
                changed_resources.add(resource_name)

        return changed_resources


    def all_resources_events_cache_file_name(self) -> str:
        return './.cache/churchtools_resource_events.json'

    def read_all_resources_events_from_cache(self) -> AllResourcesEvents:

        # step 1: Read the file. Since file is small, we are doing a whole read.
        try:
            with open(self.all_resources_events_cache_file_name(), 'r', encoding='utf-8') as stream:
                # step 2: Parse the yaml file into a dictionary
                json_str = json.load(stream) # -> Dict[Any, Any]

            # step 3: Change dictionary into class
            return AllResourcesEvents(**json_str)

        except FileNotFoundError as exc:
            return AllResourcesEvents()

        except json.JSONDecodeError as exc:
            self.logger.error(exc)
            return AllResourcesEvents()

    def write_all_resources_events_to_cache(self, all_resources_events: AllResourcesEvents) -> None:
        json_data = all_resources_events.model_dump(mode = 'json')
        json_str = json.dumps(json_data)
        cache_filename = self.all_resources_events_cache_file_name()

        os.makedirs(os.path.dirname(cache_filename), exist_ok=True)
        with open(cache_filename, "w", encoding='utf8') as text_file:
            text_file.write(json_str)
