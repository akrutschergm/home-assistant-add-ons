from datetime import date, datetime, time, timedelta
from models.events import Event
from pydantic import BaseModel
import pytz
from typing import Dict


def validate_temperature(temperature: float, required: bool = False) -> None:
    """Validates a temperature to be 0.0 or between 5.0 and 25.0 as it is required by tado.

    Args:
        temperature (float): The temperature value.
        required (bool, optional): Specifies whether the temperature may not be None. Defaults to False.

    Raises:
        ValueError: When required is True but temperature is None or wenn the temperature value is out of range.
    """
    if not temperature and required:
        raise ValueError('temperature is required but not given. Valid range: 0.0, 5.0 - 25.0')

    if temperature and \
        (temperature < 0.0 or (temperature > 0.0 and temperature < 5.0) or temperature > 25.0):
        raise ValueError('temperature not within the valid range: 0.0, 5.0 - 25.0')


class Block(BaseModel):
    """Models a PyDantic serializeable time block with start and end time and temperature.
    """
    start: time = time.min
    end: time = time.min
    temperature: float = 0.0

    def __post_init__(self):
        # todo: validate the precision of start and end time to be 5 minutes
        validate_temperature(self.temperature)


class DailySchedule(BaseModel):
    """Models a PyDantic serializeable daily schedule, which is a list of contiguous time blocks
       from 0:00 to 0:00 (which is 24:00 on the same day).

    Raises:
        ValueError: When the dictionary of time block is incomplete or contains invalid data.
    """
    blocks: Dict[time, Block] = dict({time.min: Block()})

    def __post_init__(self):
        self._validate_blocks()

    def to_string(self) -> str:
        return ', '.join([f'{b.start.strftime("%H:%M")}-{b.end.strftime("%H:%M")} {b.temperature}°C' \
            for b in self.blocks.values()])

    def _validate_blocks(self) -> None:
        """Asserts that the dictionary of time blocks is seamless from 0:00 to 0:00 (24:00).

        Raises:
            ValueError: When the dictionary of time block is incomplete.
        """
        last_end = time.min
        for k, b in self.blocks.items():
            if k != last_end:
                raise ValueError(f'expected key to equal last end time {last_end} but was {k}')
            if k != b.start:
                raise ValueError(f'expected key to equal block start time {last_end} but was {k}')
            if b.end != time.min and b.end <= b.start:
                raise ValueError(f'expected block end time {b.end} to be > start time {b.start}')
            last_end = b.end
        if last_end != time.min:
            raise ValueError(f'expected last block end time {b.end} to be {time.min}')

    def _get_previous_block_begin(self, t: time) -> time:
        return max([lt for lt in self.blocks.keys() if lt < t])

    def _get_previous_block(self, t: time) -> Block:
        last_block_begin = self._get_previous_block_begin(t)
        last_block = self.blocks.get(last_block_begin)
        return last_block


    def insert_block(self, block: Block) -> None:
        #print(f'adding time block starting {from_} ending {to}, temperature {temperature}')

        # Für Beginn und Ende: Wenn an der Stelle noch keine Trennung vorliegt, und Temperatur der
        # Zeitscheibe < Ziel-Temperatur des Termins, dann trennen Zeitscheibe
        if not self.blocks.get(block.end):
            b = self._get_previous_block(block.end)
            if block.temperature != b.temperature:
                #print(f'inserting time block starting {to} ending {b.end}, temperature {b.temperature}')
                # insert a new block, beginning with the end time
                self.blocks[block.end] = Block(start = block.end, end = b.end, temperature = b.temperature)
                # shorten the timespan of the preceeding time block
                b.end = block.end
            elif block.end < b.end:
                block.end = b.end

        if not self.blocks.get(block.start):
            b = self._get_previous_block(block.start)
            if block.temperature != b.temperature:
                #print(f'inserting time block starting {from_} ending {to}, temperature {temperature}')
                # insert a new block
                self.blocks[block.start] = block
                # shorten the timespan of the preceeding time block
                b.end = block.start
            elif b.end < block.end:
                #print(f'changing time block starting {b.start} ending {to}, temperature {temperature}')
                b.end = block.end
        else:
            b = self.blocks.get(block.start)
            #print(f'changing time block starting {b.start} ending {to}, temperature {temperature}')
            b.temperature = block.temperature
            b.end = block.end

        # Alle dazwischen liegenden Zeitscheiben löschen.
        for t in list([t for t in self.blocks.keys() if t > block.start and t < block.end]):
            #b = self.blocks[t]
            #print(f'deleting time block starting {t} ending {b.end}, temperature {b.temperature}')
            del self.blocks[t]

        self.blocks = dict(sorted(self.blocks.items()))

        # validate
        self._validate_blocks()


    def delete(self, t: time) -> None:
        if t == time.min or not self.blocks.get(t):
            return

        block = self.blocks.get(t)
        self._get_previous_block(t).end = block.end
        del self.blocks[t]

        # validate
        self._validate_blocks()


    def optimize(self) -> None:
        for t in list([t for t in self.blocks.keys() if t != time()]):
            block = self.blocks[t]
            previous_block = self._get_previous_block(t)
            if block.temperature == previous_block.temperature:
                self.delete(t)
            else:
                total_minutes = block.end.total_minutes() - block.start.total_minutes()
                if block.temperature < previous_block.temperature and \
                    total_minutes > 0 and total_minutes <= 60:
                    self.delete(t)

        # validate
        self._validate_blocks()


    @classmethod
    def from_events(cls, date_: date, events: list[Event], warm: float,
                    cold: float = None, earlystart: time = None):

        validate_temperature(warm, required = True)
        validate_temperature(cold)

        cold = cold or 0.0
        earlystart = earlystart or time.min

        utc=pytz.UTC
        from_ = utc.localize(datetime.combine(date_, time.min))
        to = from_ + timedelta(days=1)

        events = list([e for e in events if e.start < to and e.end > from_])
        schedule = DailySchedule(weekday = date_.weekday(),
                                 blocks = { time.min: Block(temperature = cold)})

        for e in events:
            begin_ = time.min if e.start <= from_ else e.start.time()
            begin_ = time.min if begin_ <= earlystart else \
                (datetime.combine(date_, begin_) - timedelta(hours = earlystart.hour, minutes = earlystart.minute)).time()
            end_ = time.min if e.end >= to else e.end.time()
            schedule.insert_block(Block(start = begin_, end = end_, temperature = warm))

        return schedule
