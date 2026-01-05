import sys
from pathlib import Path

# Add schedules directory to path to import models
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from datetime import date, datetime, time
import pytz
from models.events import Event
from models.schedules import DailySchedule, Block
import unittest


class TestDailyScheduleFromEvents(unittest.TestCase):
    """Test cases for DailySchedule.from_events method"""

    def setUp(self):
        """Set up test fixtures"""
        self.maxDiff = None
        self.events = [
            Event(
                start=datetime(2025, 1, 19, 19, 0, tzinfo=pytz.UTC),
                end=datetime(2025, 1, 20, 1, 0, tzinfo=pytz.UTC),
                name="Meeting"),
            Event(
                start=datetime(2025, 1, 20, 9, 0, tzinfo=pytz.UTC),
                end=datetime(2025, 1, 20, 17, 0, tzinfo=pytz.UTC),
                name="Meeting"),
            Event(
                start=datetime(2025, 1, 20, 19, 0, tzinfo=pytz.UTC),
                end=datetime(2025, 1, 21, 1, 0, tzinfo=pytz.UTC),
                name="Meeting"),
        ]

    def run_test(self, date_: date, expected_blocks: dict, events: list[Event] = None,
                 warm: float = 22.0, cold: float = None, earlystart: time = None):
        """Helper method to run a test case"""
        schedule = DailySchedule.from_events(
            date_=date_,
            events=events or self.events,
            warm=warm,
            cold=cold,
            earlystart=earlystart
        )
        
        expected = DailySchedule(blocks=expected_blocks)
        print ("expected: " + expected.to_string())
        print ("actual:   " + schedule.to_string())

        self.assertIsNotNone(schedule)
        self.assertIsInstance(schedule, DailySchedule)
        self.assertEqual(schedule.blocks, expected.blocks)

    def test_schedule_minutes_precision_handling(self):
        """Test schedule creation with events having 5 minute precision"""
        events = [
            Event(
                start=datetime(2025, 1, 22, 10, 7, tzinfo=pytz.UTC),
                end=datetime(2025, 1, 22, 10, 53, tzinfo=pytz.UTC),
                name="Meeting")]
        expected_blocks={
            time(0, 0): Block(start=time(0, 0), end=time(10, 5), temperature=0.0),
            time(10, 5): Block(start=time(10, 5), end=time(10, 55), temperature=22.0),
            time(10, 55): Block(start=time(10, 55), end=time(0, 0), temperature=0.0),
        }
        self.run_test(date(2025, 1, 22), expected_blocks, events)
        
    def test_sunday_schedule_with_evening_event(self):
        """Test schedule for Sunday Jan 19 which has an evening event"""
        expected_blocks={
            time(0, 0): Block(start=time(0, 0), end=time(19, 0), temperature=0.0),
            time(19, 0): Block(start=time(19, 0), end=time(0, 0), temperature=22.0),
        }
        self.run_test(date(2025, 1, 19), expected_blocks)

    def test_monday_schedule_with_two_events(self):
        """Test schedule for Monday Jan 20 which has day and evening events"""
        expected_blocks={
            time(0, 0): Block(start=time(0, 0), end=time(1, 0), temperature=22.0),
            time(1, 0): Block(start=time(1, 0), end=time(9, 0), temperature=0.0),
            time(9, 0): Block(start=time(9, 0), end=time(17, 0), temperature=22.0),
            time(17, 0): Block(start=time(17, 0), end=time(19, 0), temperature=0.0),
            time(19, 0): Block(start=time(19, 0), end=time(0, 0), temperature=22.0),
        }
        self.run_test(date(2025, 1, 20), expected_blocks)

    def test_monday_schedule_with_earlystart(self):
        """Test schedule for Monday Jan 20 with earlystart"""
        expected_blocks={
            time(0, 0): Block(start=time(0, 0), end=time(1, 0), temperature=22.0),
            time(1, 0): Block(start=time(1, 0), end=time(7, 0), temperature=0.0),
            time(7, 0): Block(start=time(7, 0), end=time(17, 0), temperature=22.0),
            time(17, 0): Block(start=time(17, 0), end=time(0, 0), temperature=22.0),
        }
        self.run_test(date(2025, 1, 20), expected_blocks, earlystart=time(2, 0))

    def test_monday_schedule_with_overlaping_earlystart(self):
        """Test schedule for Monday Jan 20 with earlystart"""
        expected_blocks={
            time(0, 0): Block(start=time(0, 0), end=time(1, 0), temperature=22.0),
            time(1, 0): Block(start=time(1, 0), end=time(6, 0), temperature=0.0),
            time(6, 0): Block(start=time(6, 0), end=time(0, 0), temperature=22.0),
        }
        self.run_test(date(2025, 1, 20), expected_blocks, earlystart=time(3, 0))

    def test_tuesday_schedule_with_event_spanning_day(self):
        """Test schedule for Tuesday Jan 21 which has event starting at midnight"""
        expected_blocks={
            time(0, 0): Block(start=time(0, 0), end=time(1, 0), temperature=22.0),
            time(1, 0): Block(start=time(1, 0), end=time(0, 0), temperature=0.0),
        }
        self.run_test(date(2025, 1, 21), expected_blocks)

    def test_schedule_with_custom_cold_temperature(self):
        """Test that custom cold temperature is respected"""
        cold_temp = 10.0
        schedule = DailySchedule.from_events(
            date_=date(2025, 1, 19),
            events=self.events,
            warm=22.0,
            cold=cold_temp
        )
        
        self.assertIsNotNone(schedule)
        
        # Verify cold blocks have the custom temperature
        cold_blocks = [b for b in schedule.blocks.values() if b.temperature == cold_temp]
        self.assertGreater(len(cold_blocks), 0)

    def test_schedule_validity(self):
        """Test that schedule is valid (blocks are contiguous from 00:00 to 00:00)"""
        schedule = DailySchedule.from_events(
            date_=date(2025, 1, 20),
            events=self.events,
            warm=22.0
        )
        
        # Should not raise ValueError during validation
        schedule._validate_blocks()
        
        # Verify schedule spans entire day
        self.assertEqual(list(schedule.blocks.keys())[0], time.min)
        self.assertEqual(list(schedule.blocks.values())[-1].end, time.min)

    def test_schedule_with_no_matching_events(self):
        """Test schedule creation when no events match the date"""
        schedule = DailySchedule.from_events(
            date_=date(2025, 1, 25),  # Date with no events
            events=self.events,
            warm=22.0
        )
        
        self.assertIsNotNone(schedule)
        # Should have at least the default cold block
        self.assertGreater(len(schedule.blocks), 0)
        
        # All blocks should be cold temperature (0.0)
        for block in schedule.blocks.values():
            self.assertEqual(block.temperature, 0.0)

    def test_schedule_string_representation(self):
        """Test that schedule can be converted to string"""
        schedule = DailySchedule.from_events(
            date_=date(2025, 1, 20),
            events=self.events,
            warm=22.0
        )
        
        schedule_str = schedule.to_string()
        self.assertIsInstance(schedule_str, str)
        self.assertGreater(len(schedule_str), 0)
        # Should contain time format and temperature
        self.assertIn(":", schedule_str)
        self.assertIn("°C", schedule_str)

    def test_multiple_schedules_match_main_output(self):
        """Test that the three main schedules are created correctly"""
        sunday = DailySchedule.from_events(
            date_=date(2025, 1, 19),
            events=self.events,
            warm=22.0
        )
        monday = DailySchedule.from_events(
            date_=date(2025, 1, 20),
            events=self.events,
            warm=22.0
        )
        tuesday = DailySchedule.from_events(
            date_=date(2025, 1, 21),
            events=self.events,
            warm=22.0
        )
        
        # All should be valid
        for schedule in [sunday, monday, tuesday]:
            self.assertIsNotNone(schedule)
            self.assertIsInstance(schedule, DailySchedule)
            schedule._validate_blocks()


if __name__ == '__main__':
    unittest.main()
