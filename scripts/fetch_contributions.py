#!/usr/bin/env python3
"""Fetch a public GitHub contribution calendar and derive profile statistics."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", default=os.getenv("GH_PROFILE_USER", "Alexsandrrh"))
    parser.add_argument("--output", type=Path, default=Path("data/contributions.json"))
    return parser.parse_args()


def fetch_days(username: str) -> list[dict[str, object]]:
    url = f"https://github.com/users/{username}/contributions"
    response = requests.get(
        url,
        headers={"User-Agent": "Alexsandrrh-profile-readme/1.0"},
        timeout=30,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    days: list[dict[str, object]] = []
    for cell in soup.select("td.ContributionCalendar-day[data-date]"):
        date = cell.get("data-date")
        tooltip = soup.find("tool-tip", attrs={"for": cell.get("id")})
        label = tooltip.get_text(" ", strip=True) if tooltip else ""
        match = re.search(r"([\d,]+) contribution", label, re.IGNORECASE)
        count = int(match.group(1).replace(",", "")) if match else 0
        days.append({"date": date, "count": count})
    days.sort(key=lambda day: str(day["date"]))
    if len(days) < 350:
        raise RuntimeError(
            f"GitHub returned only {len(days)} calendar cells; its markup may have changed"
        )
    return days


def streaks(days: list[dict[str, object]]) -> tuple[dict[str, object], dict[str, object]]:
    longest_length = current_run = 0
    longest_start = longest_end = run_start = None
    for day in days:
        if int(day["count"]) > 0:
            if current_run == 0:
                run_start = day["date"]
            current_run += 1
            if current_run > longest_length:
                longest_length = current_run
                longest_start = run_start
                longest_end = day["date"]
        else:
            current_run = 0
            run_start = None

    index = len(days) - 1
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    if index >= 0 and days[index]["date"] == today and int(days[index]["count"]) == 0:
        index -= 1
    current_length, current_end = 0, None
    while index >= 0 and int(days[index]["count"]) > 0:
        current_end = current_end or days[index]["date"]
        current_length += 1
        index -= 1
    current_start = days[index + 1]["date"] if current_length else None
    return (
        {"length": current_length, "start": current_start, "end": current_end},
        {"length": longest_length, "start": longest_start, "end": longest_end},
    )


def build_payload(username: str, days: list[dict[str, object]]) -> dict[str, object]:
    current, longest = streaks(days)
    active = [day for day in days if int(day["count"]) > 0]
    best = max(days, key=lambda day: int(day["count"]))
    return {
        "username": username,
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "range": {"start": days[0]["date"], "end": days[-1]["date"]},
        "total_contributions": sum(int(day["count"]) for day in days),
        "active_days": len(active),
        "current_streak": current,
        "longest_streak": longest,
        "best_day": best,
        "days": days,
    }


def main() -> None:
    args = parse_args()
    payload = build_payload(args.username, fetch_days(args.username))
    if args.output.exists():
        previous = json.loads(args.output.read_text(encoding="utf-8"))
        previous_comparable = {key: value for key, value in previous.items() if key != "generated_at"}
        current_comparable = {key: value for key, value in payload.items() if key != "generated_at"}
        if previous_comparable == current_comparable:
            print(f"No contribution changes; kept {args.output}")
            return
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        f"Wrote {args.output}: {payload['total_contributions']} contributions, "
        f"{payload['current_streak']['length']}-day current streak"
    )


if __name__ == "__main__":
    main()
