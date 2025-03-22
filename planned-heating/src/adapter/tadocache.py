import json
import logging
from adapter.tado import TadoAdapter, get_tado_day_type
from models.schedules import DailySchedule
from models.tadoschedules import HomeSchedules, ZoneSchedules
import os


class CachingTadoAdapter:
    logger: logging.Logger = logging.getLogger(__name__)
    current_schedules: HomeSchedules = None
    tado_adapter: TadoAdapter
    full_update: bool

    def __init__(self, tado_adapter: TadoAdapter, full_update: bool = False):
        self.tado_adapter = tado_adapter
        self.full_update = full_update

    def get_zone_id(self, zone_name: str) -> int:
        return self.tado_adapter.get_zone_id(zone_name)

    def get_zone_name(self, zone_id: int) -> str:
        return self.tado_adapter.get_zone_name(zone_id)


    def set_schedules_for_all_zones(self, home_schedules: HomeSchedules) -> None:
        if self.full_update:
            self.tado_adapter.set_schedules_for_all_zones(home_schedules)
        else:
            for zone_schedules in home_schedules.schedules.values():
                self.set_schedules_for_zone(zone_schedules)

        self._write_current_schedules_to_cache(home_schedules)


    def set_schedules_for_zone(self, zone_schedules: ZoneSchedules) -> None:
        if self.full_update:
            self.tado_adapter.set_schedules_for_zone(zone_schedules)
        else:
            current_schedules = self._get_current_schedules()
            current_zone_schedules = current_schedules.schedules[zone_schedules.name] \
                if current_schedules and zone_schedules.name in current_schedules.schedules else None

            if current_zone_schedules and zone_schedules == current_zone_schedules:
                self.logger.info('Schedule for Tado zone "%s" (%d) is up to date.', zone_schedules.name, zone_schedules.id)
            else:
                for weekday in range(0, 7):
                    schedule = zone_schedules.daily_schedules[weekday]
                    self.set_schedule_for_zone_and_day(zone_schedules.name, zone_schedules.id, weekday, schedule)


    def set_schedule_for_zone_and_day(self, zone_name: str, zone_id: int, weekday: int, schedule: DailySchedule) -> None:
        if self.full_update:
            self.tado_adapter.set_schedule_for_zone_and_day(zone_name, zone_id, weekday, schedule)
        else:
            current_schedules = self._get_current_schedules()
            current_zone_schedules = current_schedules.schedules[zone_name] \
                if current_schedules and zone_name in current_schedules.schedules else None
            current_daily_schedule = current_zone_schedules.daily_schedules[weekday] \
                if current_zone_schedules else None

            if current_daily_schedule and schedule == current_daily_schedule:
                day_type = get_tado_day_type(weekday)
                self.logger.debug('Schedule for Tado zone "%s" (%d) is up to date for %s.', zone_name, zone_id, day_type)
            else:
                self.tado_adapter.set_schedule_for_zone_and_day(zone_name, zone_id, weekday, schedule)


    def _get_current_schedules(self) -> HomeSchedules:
        if not self.current_schedules:
            self.current_schedules = self._read_current_schedules_from_cache(self._schedules_cache_file_name())

        return self.current_schedules

    def _schedules_cache_file_name(self) -> str:
        return "./.cache/tado_schedules.json"

    def _read_current_schedules_from_cache(self, file_name: str) -> HomeSchedules:
        # step 1: Read the file. Since file is small, we are doing a whole read.
        try:
            with open(file_name, 'r', encoding='utf-8') as stream:
                # step 2: Parse the yaml file into a dictionary
                json_data = json.load(stream) # -> Dict[Any, Any]

            # step 3: Change dictionary into class
            return HomeSchedules(**json_data)

        except FileNotFoundError as exc:
            return HomeSchedules()

        except json.JSONDecodeError as exc:
            self.logger.error(exc)
            return HomeSchedules()

    def _write_current_schedules_to_cache(self, home_schedules: HomeSchedules) -> None:
        json_data = home_schedules.model_dump(mode = 'json')
        json_str = json.dumps(json_data)
        file_name = self._schedules_cache_file_name()

        os.makedirs(os.path.dirname(file_name), exist_ok=True)
        with open(file_name, "w", encoding='utf8') as text_file:
            text_file.write(json_str)

        self.current_schedules = home_schedules
