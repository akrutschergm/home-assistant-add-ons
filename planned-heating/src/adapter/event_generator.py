from datetime import date, datetime, time, timedelta
from dateutil import tz
import logging
from models.events import AllCalendarEvents, Event, CalendarEvents
from models.settings import SchedulesSettings
import re
from typing import List

DAY_INDEX = {
    "Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3,
    "Fri": 4, "Sat": 5, "Sun": 6
}

RANGE_PATTERN = re.compile(r"^([A-Za-z]{3})-([A-Za-z]{3})$")
DAY_PATTERN = re.compile(r"^[A-Za-z]{3}$")


class EventGenerator:
    logger: logging.Logger = logging.getLogger(__name__)
    settings: List[SchedulesSettings]

    def __init__(self, settings: List[SchedulesSettings]):
        self.settings = settings

    def generate_events(self, day_start: date, day_end: date) -> AllCalendarEvents:
        
        all_calendars_events = AllCalendarEvents()
        for schedule_setting in self.settings:
            self.logger.debug('Generating events for schedule: %s', schedule_setting.name)

            all_calendars_events.events[schedule_setting.name] = CalendarEvents(
                name = schedule_setting.name,
                events = _generate_schedule_events(schedule_setting, day_start, day_end)
            )

        self.logger.debug('Scheduled events: %s', all_calendars_events)

        return all_calendars_events


def _generate_schedule_events(schedule: SchedulesSettings, day_start: date, day_end: date):
    active_days = _parse_days(schedule.days_of_week)
    events = []

    current_date = day_start
    while current_date <= day_end:
        if current_date.weekday() in active_days:
            events.append(Event(
                            start = datetime.combine(current_date, schedule.start).replace(tzinfo=tz.tzlocal()),
                            end = datetime.combine(current_date, schedule.end).replace(tzinfo=tz.tzlocal()),
                            name = schedule.name
                        ))
        current_date += timedelta(days=1)

    return events
    

def _parse_days(days_str: str) -> List[int]:
    """
    Parse a string like:
        "Mon-Fri"
        "Mon-Wed,Fri"
        "Mon-Tue,Thu,Fri-Sun"
    into a sorted list of weekday indexes.
    """

    days = set()

    for part in days_str.split(","):
        part = part.strip()

        # Range case: "Mon-Fri"
        m = RANGE_PATTERN.match(part)
        if m:
            d1, d2 = m.groups()
            start = DAY_INDEX[d1.capitalize()]
            end = DAY_INDEX[d2.capitalize()]

            if end < start:  # wrap-around case (Fri-Mon)
                days.update(range(start, 7))
                days.update(range(0, end + 1))
            else:
                days.update(range(start, end + 1))

            continue

        # Single day: "Tue"
        if DAY_PATTERN.match(part):
            days.add(DAY_INDEX[part.capitalize()])
            continue

        raise ValueError(f"Invalid day segment: '{part}'")

    return sorted(days)