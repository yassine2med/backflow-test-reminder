"""Backflow preventer annual test tracking: due dates and status."""
from __future__ import annotations

import csv
import calendar
from dataclasses import dataclass
from datetime import date
from pathlib import Path

REQUIRED_COLUMNS = ("device_id", "location", "last_test_date")


@dataclass(frozen=True)
class Device:
    """One backflow preventer assembly."""

    device_id: str
    location: str
    last_test: date
    interval_months: int = 12
    vendor: str = ""


@dataclass(frozen=True)
class Result:
    """Status of one device on a given day."""

    device: Device
    due: date
    days_left: int
    status: str


def add_months(start: date, months: int) -> date:
    """Return start plus whole months, clamping to the last day of the month."""
    index = start.month - 1 + months
    year, month = start.year + index // 12, index % 12 + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def evaluate(device: Device, today: date, warn_days: int = 30) -> Result:
    """Compute due date and status: OVERDUE, DUE SOON or OK."""
    if device.interval_months < 1:
        raise ValueError(f"{device.device_id}: interval_months must be 1 or more")
    due = add_months(device.last_test, device.interval_months)
    left = (due - today).days
    if left < 0:
        status = "OVERDUE"
    elif left <= warn_days:
        status = "DUE SOON"
    else:
        status = "OK"
    return Result(device, due, left, status)


def load_devices(path: Path) -> list[Device]:
    """Read devices from a CSV file. Raises ValueError on bad rows."""
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"missing columns: {', '.join(missing)}")
        devices = []
        for line_no, row in enumerate(reader, start=2):
            try:
                last = date.fromisoformat(row["last_test_date"].strip())
                months = int((row.get("interval_months") or "12").strip())
            except ValueError as exc:
                raise ValueError(f"line {line_no}: {exc}") from exc
            devices.append(
                Device(row["device_id"].strip(), row["location"].strip(), last,
                       months, (row.get("vendor") or "").strip())
            )
    return devices


def report(devices: list[Device], today: date, warn_days: int = 30) -> list[Result]:
    """Evaluate all devices, most urgent first."""
    results = [evaluate(d, today, warn_days) for d in devices]
    return sorted(results, key=lambda r: r.days_left)


def format_table(results: list[Result]) -> str:
    """Render results as a fixed-width text table."""
    head = f"{'DEVICE':<8} {'LOCATION':<28} {'DUE':<11} {'DAYS':>5}  STATUS"
    lines = [head]
    for r in results:
        lines.append(
            f"{r.device.device_id:<8} {r.device.location:<28} {r.due.isoformat():<11} "
            f"{r.days_left:>5}  {r.status}"
        )
    return "\n".join(lines)
