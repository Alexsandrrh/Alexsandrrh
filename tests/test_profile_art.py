from __future__ import annotations

import json
import sys
import tempfile
import unittest
import datetime as dt
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import fetch_contributions  # noqa: E402
import render_contributions  # noqa: E402


class ContributionDataTests(unittest.TestCase):
    def test_streaks_allow_an_empty_current_day(self) -> None:
        today = dt.datetime.now(dt.timezone.utc).date()
        days = [
            {"date": (today - dt.timedelta(days=3)).isoformat(), "count": 0},
            {"date": (today - dt.timedelta(days=2)).isoformat(), "count": 2},
            {"date": (today - dt.timedelta(days=1)).isoformat(), "count": 1},
            {"date": today.isoformat(), "count": 0},
        ]
        current, longest = fetch_contributions.streaks(days)
        self.assertEqual(current["length"], 2)
        self.assertEqual(current["start"], (today - dt.timedelta(days=2)).isoformat())
        self.assertEqual(longest["length"], 2)

    def test_grid_starts_on_sunday_and_has_full_weeks(self) -> None:
        days = [
            {"date": "2026-07-13", "count": 1},  # Monday
            {"date": "2026-07-14", "count": 0},
        ]
        columns = render_contributions.grid(days)
        self.assertIsNone(columns[0][0])
        self.assertEqual(columns[0][1]["date"], "2026-07-13")
        self.assertEqual(len(columns[0]), 7)

    def test_render_is_accessible_and_has_reduced_motion(self) -> None:
        payload = json.loads((ROOT / "data" / "contributions.json").read_text())
        svg = render_contributions.render(payload)
        self.assertIn('role="img"', svg)
        self.assertIn("prefers-reduced-motion", svg)
        self.assertEqual(svg.count('class="cell"'), len(payload["days"]))
        self.assertNotIn("<script", svg)
        self.assertNotIn("<image", svg)
        self.assertNotIn('href="http', svg)

    def test_generated_svg_round_trips_as_utf8(self) -> None:
        payload = json.loads((ROOT / "data" / "contributions.json").read_text())
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "calendar.svg"
            output.write_text(render_contributions.render(payload), encoding="utf-8")
            self.assertTrue(output.read_bytes().startswith(b"<svg"))


if __name__ == "__main__":
    unittest.main()
