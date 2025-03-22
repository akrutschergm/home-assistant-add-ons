from datetime import time
import logging

import PyTado.interface
from models.schedules import DailySchedule
from models.tadoschedules import HomeSchedules, ZoneSchedules
from PyTado.interface import Tado
import PyTado.const


def get_tado_day_type(weekday: int) -> str:
    return ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY'][weekday]

def _to_tado_schedule(day_type: str, schedule: DailySchedule) -> list[any]:

    def _celsius_to_fahrenheit(celsius: float) -> float:
        return (celsius * 1.8) + 32.0

    def _create_time_block(day_type: str, start: time, end: time, temperature: float) -> dict:
        return {
            'dayType': day_type,
            'start': start.strftime('%H:%M'),
            'end': end.strftime('%H:%M'),
            'geolocationOverride': False,
            'setting': {
                'type': PyTado.const.TYPE_HEATING,
                'power': 'OFF' if temperature < 5.0 else 'ON',
                'temperature': None if temperature < 5.0 else {
                    'celsius': temperature,
                    'fahrenheit': _celsius_to_fahrenheit(temperature)
                }
            }
        }

    return list([_create_time_block(day_type, b.start, b.end, b.temperature) \
        for b in schedule.blocks.values()])

class TadoAdapter:
    logger: logging.Logger = logging.getLogger(__name__)
    tado: Tado = None
    zone_ids: dict[str: int] = None

    TIMETABLE_MON_TO_SUN = 0
    TIMETABLE_MON_TO_FRI_SAT_SUN = 1
    TIMETABLE_MON_TUE_WED_THU_FRI_SAT_SUN = 2

    # DAY_TYPE_MONDAY_TO_SUNDAY = 'MONDAY_TO_SUNDAY'
    # DAY_TYPE_MONDAY_TO_FRIDAY = 'MONDAY_TO_FRIDAY'
    # DAY_TYPE_MONDAY = 'MONDAY'
    # DAY_TYPE_TUESDAY = 'TUESDAY'
    # DAY_TYPE_WEDNESDAY = 'WEDNESDAY'
    # DAY_TYPE_THURSDAY = 'THURSDAY'
    # DAY_TYPE_FRIDAY = 'FRIDAY'
    # DAY_TYPE_SATURDAY = 'SATURDAY'
    # DAY_TYPE_SUNDAY = 'SUNDAY'

    def __init__(self):
        self.tado = self._activate_device()
        self.zone_ids = self._get_zone_ids()

    def _activate_device(self) -> Tado:
        tado = Tado()
        self.logger.info("Device activation status: %s", tado.device_activation_status())
        self.logger.warning("ATTENTION: Please activate this device using the verification URL: %s", tado.device_verification_url())

        tado.device_activation()

        self.logger.info("Device activation status: %s", tado.device_activation_status())
        return tado

    def _get_zone_ids(self) -> dict[str: int]:
        self.logger.debug('Gettings zones')

        zones = self.tado.get_zones()
        self.logger.debug('Tado zones: %s', zones)

        zone_ids = { z.get('name') : z.get('id') for z in zones }
        self.logger.info('Tado zones: %s', zone_ids)
        return zone_ids

    def get_zone_id(self, zone_name: str) -> int:
        return self.zone_ids[zone_name]

    def get_zone_name(self, zone_id: int) -> str:
        return next(name for name, id in self.zone_ids.items() if id == zone_id)


    def set_schedules_for_all_zones(self, home_schedules: HomeSchedules) -> None:
        for zone_schedules in home_schedules.schedules.values():
            self.set_schedules_for_zone(zone_schedules)


    def set_schedules_for_zone(self, zone_schedules: ZoneSchedules) -> None:
        self.logger.info('Setting schedule for Tado zone "%s" (%d)', zone_schedules.name, zone_schedules.id)

        for weekday in range(0, 7):
            schedule = zone_schedules.daily_schedules[weekday]
            self.set_schedule_for_zone_and_day(zone_schedules.name, zone_schedules.id, weekday, schedule)

        result = self.tado.set_timetable(zone_schedules.id, 2) # timetable: 2 = Tado.Timetable.SEVEN_DAY
        self.logger.debug('result: %s', result)


    def set_schedule_for_zone_and_day(self, zone_name: str, zone_id: int, weekday: int, schedule: DailySchedule) -> None:
        day_type = get_tado_day_type(weekday)
        self.logger.info('Setting schedule for Tado zone "%s" (%d) for %s', zone_name, zone_id, day_type)

        tado_schedule = _to_tado_schedule(day_type, schedule)
        self.logger.debug('Schedule: %s', tado_schedule)

        result = self.tado.set_schedule(zone_id, 2, day_type, tado_schedule) # timetable: 2 = Tado.Timetable.SEVEN_DAY
        self.logger.debug('result: %s', result)
