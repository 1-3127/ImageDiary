from datetime import datetime
from unittest import TestCase

from capture_scheduler import next_capture_time


class NextCaptureTimeTests(TestCase):
    def test_fifteen_minute_boundary(self) -> None:
        now = datetime(2026, 8, 25, 19, 7, 12)
        self.assertEqual(next_capture_time(now, 15), datetime(2026, 8, 25, 19, 15))

    def test_exact_boundary_moves_to_next_boundary(self) -> None:
        now = datetime(2026, 8, 25, 19, 15)
        self.assertEqual(next_capture_time(now, 15), datetime(2026, 8, 25, 19, 30))

    def test_thirty_minute_hour_rollover(self) -> None:
        now = datetime(2026, 8, 25, 19, 45)
        self.assertEqual(next_capture_time(now, 30), datetime(2026, 8, 25, 20, 0))

    def test_rejects_unsupported_interval(self) -> None:
        with self.assertRaises(ValueError):
            next_capture_time(datetime(2026, 8, 25, 19, 7), 20)
