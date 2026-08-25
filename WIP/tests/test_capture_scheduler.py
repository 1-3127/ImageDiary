from datetime import datetime
from unittest import TestCase

from capture_scheduler import next_capture_time


class NextCaptureTimeTests(TestCase):
    def test_fifteen_minute_system_boundary(self) -> None:
        now = datetime(2026, 8, 25, 19, 7, 12)
        self.assertEqual(next_capture_time(now, 15 * 60), datetime(2026, 8, 25, 19, 15))

    def test_ten_minute_interval(self) -> None:
        now = datetime(2026, 8, 25, 19, 15)
        self.assertEqual(next_capture_time(now, 10 * 60), datetime(2026, 8, 25, 19, 20))

    def test_thirty_minute_hour_rollover(self) -> None:
        now = datetime(2026, 8, 25, 19, 45)
        self.assertEqual(next_capture_time(now, 30 * 60), datetime(2026, 8, 25, 20, 0))

    def test_twenty_five_minute_interval(self) -> None:
        now = datetime(2026, 8, 25, 19, 7, 12)
        self.assertEqual(next_capture_time(now, 25 * 60), datetime(2026, 8, 25, 19, 10))

    def test_one_minute_debug_boundary(self) -> None:
        now = datetime(2026, 8, 25, 19, 7, 12)
        self.assertEqual(next_capture_time(now, 60), datetime(2026, 8, 25, 19, 8))

    def test_rejects_unsupported_interval(self) -> None:
        with self.assertRaises(ValueError):
            next_capture_time(datetime(2026, 8, 25, 19, 7), 20)
