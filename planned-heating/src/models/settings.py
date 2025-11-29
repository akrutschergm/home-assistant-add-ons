
from datetime import time
import json
from pydantic import BaseModel, field_validator
from typing import List, Optional
import yaml


def validate_temperature(temperature: float, required: bool = False) -> None:
    if not temperature and required:
        raise ValueError('temperature is required but not given. Valid range: 0.0, 5.0 - 25.0')

    if temperature and \
        (temperature < 0.0 or (temperature > 0.0 and temperature < 5.0) or temperature > 25.0):
        raise ValueError('temperature not within valid range: 0.0, 5.0 - 25.0')


class HeatingSettings(BaseModel):
    cold: Optional[float] = None
    warm: Optional[float] = None
    earlystart: Optional[time] = None

    @field_validator('cold')
    def cold_temperature_in_range(cls, v):
        validate_temperature(v)
        return v

    @field_validator('warm')
    def warm_temperature_in_range(cls, v):
        validate_temperature(v, required = True)
        return v


class AssignmentSettings(HeatingSettings):
    tadozone: str
    calendar_names: List[str] = []


class SchedulesSettings(BaseModel):
    start: time
    end: time
    days_of_week: str
    name: str


class ICalSettings(BaseModel):
    source: str
    name: str


class ChurchToolsSettings(BaseModel):
    url: str


class CoreSettings(BaseModel):
    polling_minutes: Optional[int] = 15
    schedules: Optional[List[SchedulesSettings]] = None
    ical_calendars: Optional[List[ICalSettings]] = []
    churchtools: Optional[ChurchToolsSettings] = None
    heating: Optional[HeatingSettings] = None
    assignments: List[AssignmentSettings] = []

    @field_validator('polling_minutes')
    def polling_minutes_in_range(cls, v):
        if not v or (v > 60) or (60 % v):
            raise ValueError('polling_minutes must be must be a divisor of 60, i.e. 1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30 or 60')
        return v

    @classmethod
    def load_from(cls, filename: str):

        # step 1: Read the file. Since file is small, we are doing a whole read.
        if filename.endswith(".json"):
            with open(filename, 'r', encoding='utf-8') as stream:
                # step 2: Parse the yaml file into a dictionary
                config_data = json.load(stream) # -> Dict[Any, Any]

        elif filename.endswith((".yaml", ".yml")):
            with open(filename, 'r', encoding='utf-8') as stream:
                # step 2: Parse the yaml file into a dictionary
                config_data = yaml.safe_load(stream) # -> Dict[Any, Any]

        # step 3: Change dictionary into data class
        return CoreSettings(**config_data)
