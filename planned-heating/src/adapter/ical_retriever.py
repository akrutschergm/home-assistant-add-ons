from datetime import date, datetime
from dateutil import tz
from icalendar import Calendar
import json
import logging
from models.events import AllCalendarEvents, Event, CalendarEvents
from models.settings import ICalSettings
import os
from pathlib import Path
import requests
from typing import List, Optional
from urllib.parse import urlparse


class ICalRetriever:
    logger: logging.Logger = logging.getLogger(__name__)
    settings: List[ICalSettings]
    cached_calendars: Optional[list[any]] = None

    def __init__(self, settings: List[ICalSettings]):
        self.settings = settings


    def retrieve_events(self, day_start: date, day_end: date) -> tuple[AllCalendarEvents, set[str]]:
        """
        Retrieves calendar events from iCalendar sources defined in settings.
        1. Loads the iCalendar from URL or local path.
        2. Extracts events from the iCalendar.
        3. Filters events by the specified date range.
        Args:
            day_start (date): Start date of the range to filter events.
            day_end (date): End date of the range to filter events.
        Returns:
            tuple[AllCalendarsEvents, set[str]]: A tuple containing all calendar events and a set of calendar names that have updates.
        """

        all_calendars_events = AllCalendarEvents()
        for setting in self.settings:
            self.logger.debug('Retrieving calendar events from: %s', setting.source)

            # Load the iCalendar from URL or local path.
            cal = self.load_ics(setting.source)
            
            # Extract events from the iCalendar.
            events = self.get_events_from_ics(cal)

            # Filter events by the specified date range.
            events = list(filter(lambda e: e.start.date() <= day_end and e.end.date() >= day_start, events))
            
            # Store the events in the AllCalendarEvents structure.
            all_calendars_events.events[setting.name] = CalendarEvents(
                name = setting.name,
                events = events
            )

        self.logger.debug('events of all calendars in use: %s', all_calendars_events)

        # determine changes in calendar definition or events related to cached version
        calendars_having_updates = self.determine_calendars_having_updates(all_calendars_events)
        self.logger.debug('Calendars having updates: %s', calendars_having_updates if calendars_having_updates else None)

        self.write_to_cache(all_calendars_events)

        return (all_calendars_events, calendars_having_updates)


    def load_ics(self, source: str) -> Calendar:
        """
        Loads an ICS file from a URL or a local path.
        source: HTTP/HTTPS URL or local file path
        """
        parsed = urlparse(source)

        # Check if it is a URL (http or https)
        if parsed.scheme in ("http", "https"):
            response = requests.get(source)
            response.raise_for_status()
            print(response.headers)
            data = response.content  # Bytes!
        else:
            # Local path
            path = Path(source)
            data = path.read_bytes()  # Read bytes

        # Parse iCal
        return Calendar.from_ical(data)


    def get_events_from_ics(self, calendar: Calendar) -> list[Event]:
        events = []
        for component in calendar.walk():
            if component.name == "VEVENT":
                start = component.get('dtstart').dt
                end = component.get('dtend').dt
                name = str(component.get('summary'))
                
                # They may be date or datetime; force datetime if needed
                if isinstance(start, date) and not isinstance(start, datetime):
                    start = datetime.combine(start, datetime.min.time())
                if isinstance(end, date) and not isinstance(end, datetime):
                    end = datetime.combine(end, datetime.min.time())

                events.append(Event(
                    start = start.replace(tzinfo=tz.tzlocal()),
                    end = end.replace(tzinfo=tz.tzlocal()),
                    name = name))
        return events


    def determine_calendars_having_updates(self, all_calendars_events: AllCalendarEvents) -> set[str]:
        all_calendars_events_from_cache = self.read_from_cache()

        changed_calendars = set()
        for name in all_calendars_events.events:
            if (name not in all_calendars_events_from_cache.events or
                all_calendars_events.events[name] != all_calendars_events_from_cache.events[name]):
                changed_calendars.add(name)
        return changed_calendars

    def all_calendars_events_cache_file_name(self) -> str:
        return './.cache/ical_calendar_events.json'

    def read_from_cache(self) -> AllCalendarEvents:

        # step 1: Read the file. Since file is small, we are doing a whole read.
        try:
            with open(self.all_calendars_events_cache_file_name(), 'r', encoding='utf-8') as stream:
                # step 2: Parse the yaml file into a dictionary
                json_str = json.load(stream) # -> Dict[Any, Any]

            # step 3: Change dictionary into class
            return AllCalendarEvents(**json_str)

        except FileNotFoundError as exc:
            return AllCalendarEvents()

        except json.JSONDecodeError as exc:
            self.logger.error(exc)
            return AllCalendarEvents()

    def write_to_cache(self, all_calendars_events: AllCalendarEvents) -> None:
        json_data = all_calendars_events.model_dump(mode = 'json')
        json_str = json.dumps(json_data)
        cache_filename = self.all_calendars_events_cache_file_name()

        os.makedirs(os.path.dirname(cache_filename), exist_ok=True)
        with open(cache_filename, "w", encoding='utf8') as text_file:
            text_file.write(json_str)
