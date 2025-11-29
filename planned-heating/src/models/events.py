from datetime import datetime
from pydantic import BaseModel
from typing import Dict


class Event(BaseModel):
    """Models a PyDantic serializeable ChurchTools event.
    """
    start: datetime
    end: datetime
    name: str

    # todo: validate end to be > begin


class CalendarEvents(BaseModel):
    """Models a PyDantic serializeable calendar with a list of events.
    """
    name: str
    events: list[Event] = []


class AllCalendarEvents(BaseModel):
    """Models a PyDantic serializeable dictionary of calendar events.
    """
    events: Dict[str, CalendarEvents] = {}

    def select_events(self, names: list[str]) -> list[Event]:
        """Selects all events of a calendar given by their names.

        Args:
            names (list[str]): Names of the calendar, which events should be returned.

        Returns:
            list[Event]: Concateded list of events.
        """
        events = []
        for name in names:
            events.extend(self.events[name].events)
        return events
