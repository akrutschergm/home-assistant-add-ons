from datetime import time
from models.schedules import Block, DailySchedule
import unittest


class BlockTest(unittest.TestCase):
    
    def test_init_with_default_succeeds(self):
        block = Block()
        self.assertEqual(block.start, time.min)
        self.assertEqual(block.end, time.min)
        self.assertEqual(block.temperature, 0.0)
        
    def test_init_with_valid_temperature_0_succeeds(self):
        block = Block(temperature = 0.0)
        self.assertEqual(block.start, time.min)
        self.assertEqual(block.end, time.min)
        self.assertEqual(block.temperature, 0.0)
        
    def test_init_with_valid_temperature_5_succeeds(self):
        block = Block(temperature = 5.0)
        self.assertEqual(block.start, time.min)
        self.assertEqual(block.end, time.min)
        self.assertEqual(block.temperature, 5.0)
        
    def test_init_with_valid_temperature_25_succeeds(self):
        block = Block(temperature = 25.0)
        self.assertEqual(block.start, time.min)
        self.assertEqual(block.end, time.min)
        self.assertEqual(block.temperature, 25.0)
        
    def test_init_with_invalid_temperature_minus_0_1_should_fail(self):
        with self.assertRaises(ValueError):
            Block(temperature = -0.1)

    def test_init_with_invalid_temperature_0_1_should_fail(self):
        with self.assertRaises(ValueError):
            Block(temperature = 0.1)

    def test_init_with_invalid_temperature_4_9_should_fail(self):
        with self.assertRaises(ValueError):
            Block(temperature = 4.9)

    def test_init_with_invalid_temperature_25_1_should_fail(self):
        with self.assertRaises(ValueError):
            Block(temperature = 25.1)
                                         
    
class DailyScheduleTest(unittest.TestCase):
    
    # __init__
    
    def test_init_with_default_succeeds(self):
        schedule = DailySchedule()
        self.assertEqual(schedule.blocks, {time.min: Block()})

    def test_init_with_valid_temperature_0_succeeds(self):
        schedule = DailySchedule(blocks = dict({time.min: Block(temperature = 0.0)}))
        self.assertEqual(schedule.blocks, {time.min: Block()})

    def test_init_with_valid_temperature_5_succeeds(self):
        schedule = DailySchedule(blocks = dict({time.min: Block(temperature = 5.0)}))
        self.assertEqual(schedule.blocks, {time.min: Block(temperature = 5.0)})

    def test_init_with_valid_temperature_25_succeeds(self):
        schedule = DailySchedule(blocks = dict({time.min: Block(temperature = 25.0)}))
        self.assertEqual(schedule.blocks, {time.min: Block(temperature = 25.0)})

    # insert_block
    
    def test_insert_block_succeeds(self):
        schedule = DailySchedule()
        schedule.insert_block(Block(start = time(8), end = time(12), temperature = 15.0))
        print(schedule)
        
        self.assertEqual(list(schedule.blocks), [time.min, time(8), time(12)])
        
        self.assertEqual(schedule.blocks[time.min], Block(end = time(8), temperature = 0.0))
        self.assertEqual(schedule.blocks[time(8)], Block(start = time(8), end = time(12), temperature = 15.0))
        self.assertEqual(schedule.blocks[time(12)], Block(start = time(12), end = time.min, temperature = 0.0))
        
    def test_insert_continuing_block_with_different_temperature_succeeds(self):
        schedule = DailySchedule()
        schedule.insert_block(Block(start = time(8), end = time(12), temperature = 15.0))
        schedule.insert_block(Block(start = time(12), end = time(14), temperature = 20.0))
        print(schedule)
        
        self.assertEqual(list(schedule.blocks), [time.min, time(8), time(12), time(14)])
        
        self.assertEqual(schedule.blocks[time.min], Block(end = time(8), temperature = 0.0))
        self.assertEqual(schedule.blocks[time(8)], Block(start = time(8), end = time(12), temperature = 15.0))
        self.assertEqual(schedule.blocks[time(12)], Block(start = time(12), end = time(14), temperature = 20.0))
        self.assertEqual(schedule.blocks[time(14)], Block(start = time(14), end = time.min, temperature = 0.0))
        
    def test_insert_continuing_block_with_same_temperature_succeeds(self):
        schedule = DailySchedule()
        schedule.insert_block(Block(start = time(8), end = time(12), temperature = 15.0))
        schedule.insert_block(Block(start = time(12), end = time(14), temperature = 15.0))
        print(schedule)
        
        self.assertEqual(list(schedule.blocks), [time.min, time(8), time(12), time(14)])
        
        self.assertEqual(schedule.blocks[time.min], Block(end = time(8), temperature = 0.0))
        self.assertEqual(schedule.blocks[time(8)], Block(start = time(8), end = time(12), temperature = 15.0))
        self.assertEqual(schedule.blocks[time(12)], Block(start = time(12), end = time(14), temperature = 15.0))
        self.assertEqual(schedule.blocks[time(14)], Block(start = time(14), end = time.min, temperature = 0.0))
        
    def test_insert_block_after_first_succeeds(self):
        schedule = DailySchedule()
        schedule.insert_block(Block(start = time(8), end = time(12), temperature = 15.0))
        schedule.insert_block(Block(start = time(15), end = time(18), temperature = 15.0))
        print(schedule)
        
        self.assertEqual(list(schedule.blocks), [time.min, time(8), time(12), time(15), time(18)])
        
        self.assertEqual(schedule.blocks[time.min], Block(end = time(8), temperature = 0.0))
        self.assertEqual(schedule.blocks[time(8)], Block(start = time(8), end = time(12), temperature = 15.0))
        self.assertEqual(schedule.blocks[time(12)], Block(start = time(12), end = time(15), temperature = 0.0))
        self.assertEqual(schedule.blocks[time(15)], Block(start = time(15), end = time(18), temperature = 15.0))
        self.assertEqual(schedule.blocks[time(18)], Block(start = time(18), end = time.min, temperature = 0.0))
        
    def test_insert_block_before_first_succeeds(self):
        schedule = DailySchedule()
        schedule.insert_block(Block(start = time(15), end = time(18), temperature = 15.0))
        schedule.insert_block(Block(start = time(8), end = time(12), temperature = 15.0))
        print(schedule)
        
        self.assertEqual(list(schedule.blocks), [time.min, time(8), time(12), time(15), time(18)])
        
        self.assertEqual(schedule.blocks[time.min], Block(end = time(8), temperature = 0.0))
        self.assertEqual(schedule.blocks[time(8)], Block(start = time(8), end = time(12), temperature = 15.0))
        self.assertEqual(schedule.blocks[time(12)], Block(start = time(12), end = time(15), temperature = 0.0))
        self.assertEqual(schedule.blocks[time(15)], Block(start = time(15), end = time(18), temperature = 15.0))
        self.assertEqual(schedule.blocks[time(18)], Block(start = time(18), end = time.min, temperature = 0.0))
        
    def test_insert_overlapping_block_with_different_temperature_succeeds(self):
        schedule = DailySchedule()
        schedule.insert_block(Block(start = time(8), end = time(12), temperature = 15.0))
        schedule.insert_block(Block(start = time(10), end = time(15), temperature = 20.0))
        print(schedule)
        
        self.assertEqual(list(schedule.blocks), [time.min, time(8), time(10), time(15)])
        
        self.assertEqual(schedule.blocks[time.min], Block(end = time(8), temperature = 0.0))
        self.assertEqual(schedule.blocks[time(8)], Block(start = time(8), end = time(10), temperature = 15.0))
        self.assertEqual(schedule.blocks[time(10)], Block(start = time(10), end = time(15), temperature = 20.0))
        self.assertEqual(schedule.blocks[time(15)], Block(start = time(15), end = time.min, temperature = 0.0))
        
    def test_insert_block_overlapping_at_start_with_same_temperature_gets_merged(self):
        schedule = DailySchedule()
        schedule.insert_block(Block(start = time(10), end = time(15), temperature = 15.0))
        schedule.insert_block(Block(start = time(8), end = time(12), temperature = 15.0))
        print(schedule)
        
        self.assertEqual(list(schedule.blocks), [time.min, time(8), time(15)])
        
        self.assertEqual(schedule.blocks[time.min], Block(end = time(8), temperature = 0.0))
        self.assertEqual(schedule.blocks[time(8)], Block(start = time(8), end = time(15), temperature = 15.0))
        self.assertEqual(schedule.blocks[time(15)], Block(start = time(15), end = time.min, temperature = 0.0))
        
    def test_insert_block_overlapping_at_end_with_same_temperature_gets_merged(self):
        schedule = DailySchedule()
        schedule.insert_block(Block(start = time(8), end = time(12), temperature = 15.0))
        schedule.insert_block(Block(start = time(10), end = time(15), temperature = 15.0))
        print(schedule)
        
        self.assertEqual(list(schedule.blocks), [time.min, time(8), time(15)])
        
        self.assertEqual(schedule.blocks[time.min], Block(end = time(8), temperature = 0.0))
        self.assertEqual(schedule.blocks[time(8)], Block(start = time(8), end = time(15), temperature = 15.0))
        self.assertEqual(schedule.blocks[time(15)], Block(start = time(15), end = time.min, temperature = 0.0))
        
    def test_insert_block_already_included_with_same_temperature_gets_merged(self):
        schedule = DailySchedule()
        schedule.insert_block(Block(start = time(8), end = time(15), temperature = 15.0))
        schedule.insert_block(Block(start = time(10), end = time(12), temperature = 15.0))
        print(schedule)
        
        self.assertEqual(list(schedule.blocks), [time.min, time(8), time(15)])
        
        self.assertEqual(schedule.blocks[time.min], Block(end = time(8), temperature = 0.0))
        self.assertEqual(schedule.blocks[time(8)], Block(start = time(8), end = time(15), temperature = 15.0))
        self.assertEqual(schedule.blocks[time(15)], Block(start = time(15), end = time.min, temperature = 0.0))
        
