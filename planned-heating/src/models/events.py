from datetime import datetime
from pydantic import BaseModel
from typing import Dict


class Event(BaseModel):
    begin: datetime
    end: datetime
    name: str

    # todo: validate end to be > begin
    

class ResourceEvents(BaseModel):
    name: str
    id: int
    events: list[Event] = []


class AllResourcesEvents(BaseModel):
    resource_events: Dict[str, ResourceEvents] = {}

    def select_events(self, resource_names: list[str]) -> list[Event]:
        events = []
        for resource_name in resource_names:
            events.extend(self.resource_events[resource_name].events)
        return events
