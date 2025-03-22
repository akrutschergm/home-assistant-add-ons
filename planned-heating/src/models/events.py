from datetime import datetime
from pydantic import BaseModel
from typing import Dict


class Event(BaseModel):
    """Models a PyDantic serializeable ChurchTools event.
    """
    begin: datetime
    end: datetime
    name: str

    # todo: validate end to be > begin


class ResourceEvents(BaseModel):
    """Models a PyDantic serializeable ChurchTools resource with a list of Events.
    """
    name: str
    id: int
    events: list[Event] = []


class AllResourcesEvents(BaseModel):
    """Models a PyDantic serializeable dictionary of ChurchTools resources and Events.
    """
    resource_events: Dict[str, ResourceEvents] = {}

    def select_events(self, resource_names: list[str]) -> list[Event]:
        """Selects all events of ChurchTools resources given by their names.

        Args:
            resource_names (list[str]): Names of the ChurchTools resources, which events should be returned.

        Returns:
            list[Event]: Concateded list of events.
        """
        events = []
        for resource_name in resource_names:
            events.extend(self.resource_events[resource_name].events)
        return events
