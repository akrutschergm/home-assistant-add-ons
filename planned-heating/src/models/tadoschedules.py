from pydantic import BaseModel
from typing import Dict
from models.schedules import DailySchedule


class ZoneSchedules(BaseModel):
    name: str
    id: int
    daily_schedules: list[DailySchedule] = list([DailySchedule() for _ in range(0, 7)])
    
    
class HomeSchedules(BaseModel):
    schedules: Dict[str, ZoneSchedules] = {}
    
    def insert(self, zone_schedules: ZoneSchedules) -> None:
        self.schedules[zone_schedules.name] = zone_schedules
