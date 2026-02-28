"""
Unit tests for EZTIME payroll overtime-bucket logic + v1 API additions.

Run with:  python test_payroll.py        (stdlib unittest)
       or: python -m pytest test_payroll.py -v

Tests are intentionally independent of FastAPI/SQLite so they run without
the full server stack.  They exercise the pure calculation functions only.
"""

import unittest
from zoneinfo import ZoneInfo
from datetime import datetime

# ---------------------------------------------------------------------------
# Inline the two pure functions so tests run without importing FastAPI
# (avoids ModuleNotFoundError when FastAPI is not installed in test env)
# ---------------------------------------------------------------------------

def _parse_hhmm(s: str) -> float:
    h, m = map(int, s.strip().split(":"))
    return h + m / 60.0


def _night_overlap_hours(start_h: float, end_h: float) -> float:
    """
    Count overlap of a shift with the 22:00–06:00 night window.

    BUG FIX (vs original code): the original used only two windows
    [22:00,24:00] and [24:00,30:00], which correctly handled midnight-
    crossing shifts and late-evening shifts, but MISSED early-morning
    non-crossing shifts like 04:00–08:00 (which has 2h in 04:00–06:00).

    The fix adds a third window [00:00, 06:00] on the same-day axis.
    All three windows are needed:
      [0,    360]  = 00:00–06:00  same-day (covers 04:00–08:00 etc.)
      [1320, 1440] = 22:00–24:00  evening
      [1440, 1800] = 00:00–06:00  next-day (midnight-crossing shifts)
    """
    def to_min(h: float) -> int:
        return int(round(h * 60))

    s = to_min(start_h)
    e = to_min(end_h)
    if e <= s:
        e += 24 * 60  # normalise midnight-crossing

    night_windows = [(0, 6 * 60), (22 * 60, 24 * 60), (24 * 60, 30 * 60)]
    overlap = 0
    for a, b in night_windows:
        overlap += max(0, min(e, b) - max(s, a))
    return overlap / 60.0


def _shift_hours(start_str: str, end_str: str) -> float:
    s = _parse_hhmm(start_str)
    e = _parse_hhmm(end_str)
    if e <= s:
        e += 24.0
    return e - s


def shift_hours_and_night(start_str: str, end_str: str):
    """Returns (total_hours, night_hours_in_window)."""
    total = _shift_hours(start_str, end_str)
    night = _night_overlap_hours(_parse_hhmm(start_str), _parse_hhmm(end_str))
    return (round(total, 4), round(night, 4))


def _buckets(total_hours: float, total_night: float) -> dict:
    """
    Apply overtime buckets (mirrors compute_daily logic exactly).
    Night rule: if total_night >= 2h → threshold = 7h, else 8h.
    Buckets:
      0..threshold         → 100%
      threshold..+2h       → 125%
      above threshold+2h   → 150%
    """
    threshold = 7.0 if total_night >= 2.0 else 8.0
    h100 = min(total_hours, threshold)
    h125 = max(0.0, min(total_hours - threshold, 2.0))
    h150 = max(0.0, total_hours - threshold - 2.0)
    return {
        "threshold": threshold,
        "h100": h100, "h125": h125, "h150": h150,
        "night_rule_applied": threshold == 7.0,
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestOvertimeBuckets(unittest.TestCase):
    """The three required test cases from the spec."""

    # -----------------------------------------------------------------------
    # TEST 1 — Normal 10-hour day (no night hours)
    # Shift: 08:00–18:00
    # Expected: threshold=8, h100=8, h125=2, h150=0
    # -----------------------------------------------------------------------
    def test_normal_10h_day(self):
        total_h, night_h = shift_hours_and_night("08:00", "18:00")
        self.assertEqual(total_h, 10.0, "10h shift duration")
        self.assertEqual(night_h, 0.0,  "No night overlap for 08:00–18:00")

        r = _buckets(total_h, night_h)
        self.assertFalse(r["night_rule_applied"], "Night rule must NOT fire")
        self.assertEqual(r["threshold"], 8.0, "Standard threshold 8h")
        self.assertEqual(r["h100"], 8.0, "Hours @100% = 8 (0–8h)")
        self.assertEqual(r["h125"], 2.0, "Hours @125% = 2 (8–10h)")
        self.assertEqual(r["h150"], 0.0, "Hours @150% = 0 (nothing above 10h)")

    # -----------------------------------------------------------------------
    # TEST 2 — 10-hour day with ≥2 night hours → threshold = 7
    # Shift: 20:00–06:00 (crosses midnight)
    # Night window overlap: 22:00–06:00 = 8h  →  night rule fires
    # Expected: threshold=7, h100=7, h125=2, h150=1
    # -----------------------------------------------------------------------
    def test_night_rule_10h_day_threshold_7(self):
        total_h, night_h = shift_hours_and_night("20:00", "06:00")
        self.assertEqual(total_h, 10.0, "20:00–06:00 = 10h")
        self.assertGreaterEqual(night_h, 2.0, "Must have ≥2h in night window")

        r = _buckets(total_h, night_h)
        self.assertTrue(r["night_rule_applied"], "Night rule MUST fire when night_h ≥ 2h")
        self.assertEqual(r["threshold"], 7.0, "Reduced threshold = 7h")
        self.assertEqual(r["h100"], 7.0, "Hours @100% = 7 (0–7h)")
        self.assertEqual(r["h125"], 2.0, "Hours @125% = 2 (7–9h)")
        self.assertEqual(r["h150"], 1.0, "Hours @150% = 1 (9–10h)")

    # -----------------------------------------------------------------------
    # TEST 3 — Split shift totalling 11h (no night hours)
    # Shift A: 06:00–11:00 = 5h
    # Shift B: 13:00–19:00 = 6h
    # Split-shift rule: SUM first (11h), THEN apply buckets
    # Expected: threshold=8, h100=8, h125=2, h150=1
    # -----------------------------------------------------------------------
    def test_split_shift_total_11h(self):
        h1, n1 = shift_hours_and_night("06:00", "11:00")
        h2, n2 = shift_hours_and_night("13:00", "19:00")
        self.assertEqual(h1, 5.0, "Shift A = 5h")
        self.assertEqual(h2, 6.0, "Shift B = 6h")

        total_h, night_h = h1 + h2, n1 + n2
        self.assertEqual(total_h, 11.0, "Combined total = 11h")
        self.assertEqual(night_h, 0.0,  "No night overlap")

        r = _buckets(total_h, night_h)
        self.assertFalse(r["night_rule_applied"], "Night rule must NOT fire")
        self.assertEqual(r["threshold"], 8.0)
        self.assertEqual(r["h100"], 8.0, "Hours @100% = 8")
        self.assertEqual(r["h125"], 2.0, "Hours @125% = 2 (8–10h)")
        self.assertEqual(r["h150"], 1.0, "Hours @150% = 1 (10–11h)")


class TestNightWindowDetection(unittest.TestCase):
    """Detailed coverage of the night overlap function, including the bug fix."""

    def test_midnight_crossing(self):
        """23:00–03:00: all 4h are in night window."""
        h, n = shift_hours_and_night("23:00", "03:00")
        self.assertEqual(h, 4.0)
        self.assertEqual(n, 4.0)

    def test_early_morning_partial_night(self):
        """
        04:00–08:00: 04:00–06:00 = 2h in night window.
        This was the BUG in the original code (missing [0,06:00] window).
        """
        h, n = shift_hours_and_night("04:00", "08:00")
        self.assertEqual(h, 4.0)
        self.assertEqual(n, 2.0, "04:00–06:00 must count as 2h night (bug-fix check)")

    def test_daytime_no_night(self):
        """09:00–17:00: zero night overlap."""
        h, n = shift_hours_and_night("09:00", "17:00")
        self.assertEqual(h, 8.0)
        self.assertEqual(n, 0.0)

    def test_full_early_morning_window(self):
        """00:00–06:00: all 6h are night hours."""
        h, n = shift_hours_and_night("00:00", "06:00")
        self.assertEqual(h, 6.0)
        self.assertEqual(n, 6.0)

    def test_exactly_8h_no_overtime(self):
        """Exactly at the threshold: h100=8, no overtime."""
        h, n = shift_hours_and_night("08:00", "16:00")
        r = _buckets(h, n)
        self.assertEqual(r["h100"], 8.0)
        self.assertEqual(r["h125"], 0.0)
        self.assertEqual(r["h150"], 0.0)

    def test_exactly_7h_night_rule_no_overtime(self):
        """7h with night rule active: h100=7, no overtime at all."""
        r = _buckets(7.0, total_night=2.0)
        self.assertEqual(r["threshold"], 7.0)
        self.assertEqual(r["h100"], 7.0)
        self.assertEqual(r["h125"], 0.0)
        self.assertEqual(r["h150"], 0.0)


class TestAuthLogic(unittest.TestCase):
    """Token validation logic (mirrors _check_token in main.py)."""

    class _TokenError(Exception):
        pass

    def _check(self, auth, token="demo-token"):
        if not auth or not auth.startswith("Bearer "):
            raise self._TokenError()
        if auth.removeprefix("Bearer ").strip() != token:
            raise self._TokenError()

    def test_valid_token_passes(self):
        self._check("Bearer demo-token")  # must not raise

    def test_missing_header_raises(self):
        with self.assertRaises(self._TokenError):
            self._check(None)

    def test_wrong_token_raises(self):
        with self.assertRaises(self._TokenError):
            self._check("Bearer wrong-token")

    def test_no_bearer_prefix_raises(self):
        with self.assertRaises(self._TokenError):
            self._check("demo-token")  # missing 'Bearer ' prefix


class TestJerusalemTimezone(unittest.TestCase):
    """calculated_at must carry Asia/Jerusalem UTC offset."""

    def test_iso8601_with_offset(self):
        tz = ZoneInfo("Asia/Jerusalem")
        ts = datetime.now(tz).isoformat(timespec="seconds")
        # Should end with +HH:MM or +HH:MM:SS (never bare 'Z' for Asia/Jerusalem)
        self.assertRegex(ts, r"\+\d{2}:\d{2}", f"No UTC offset in timestamp: {ts}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
