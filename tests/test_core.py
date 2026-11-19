from datetime import date

import pytest

from backflow_reminder.__main__ import main
from backflow_reminder.core import (Device, add_months, evaluate, format_table,
                                    load_devices, report)

TODAY = date(2026, 11, 19)


def dev(last, months=12, ident="X1"):
    return Device(ident, "Loc", last, months)


def test_add_months_simple():
    assert add_months(date(2025, 3, 10), 12) == date(2026, 3, 10)


def test_add_months_clamps_leap_day():
    assert add_months(date(2024, 2, 29), 12) == date(2025, 2, 28)


def test_add_months_crosses_year():
    assert add_months(date(2025, 11, 30), 3) == date(2026, 2, 28)


def test_overdue():
    r = evaluate(dev(date(2025, 6, 1)), TODAY)
    assert r.status == "OVERDUE" and r.days_left < 0


def test_due_soon_boundary():
    r = evaluate(dev(date(2025, 12, 19)), TODAY, warn_days=30)
    assert r.days_left == 30 and r.status == "DUE SOON"


def test_ok_beyond_warning():
    assert evaluate(dev(date(2026, 8, 1)), TODAY).status == "OK"


def test_due_today_is_due_soon_not_overdue():
    r = evaluate(dev(date(2025, 11, 19)), TODAY)
    assert r.days_left == 0 and r.status == "DUE SOON"


def test_bad_interval_rejected():
    with pytest.raises(ValueError):
        evaluate(dev(date(2026, 1, 1), months=0), TODAY)


def test_report_sorted_most_urgent_first():
    out = report([dev(date(2026, 8, 1), ident="A"), dev(date(2025, 1, 1), ident="B")], TODAY)
    assert [r.device.device_id for r in out] == ["B", "A"]


def test_load_example_file():
    devices = load_devices(__import__("pathlib").Path("examples/devices.csv"))
    assert len(devices) == 6 and devices[4].interval_months == 6


def test_load_missing_column(tmp_path):
    f = tmp_path / "bad.csv"
    f.write_text("device_id,location\nA,B\n")
    with pytest.raises(ValueError, match="missing columns"):
        load_devices(f)


def test_load_bad_date(tmp_path):
    f = tmp_path / "bad.csv"
    f.write_text("device_id,location,last_test_date\nA,B,not-a-date\n")
    with pytest.raises(ValueError, match="line 2"):
        load_devices(f)


def test_table_contains_status():
    text = format_table(report([dev(date(2025, 1, 1))], TODAY))
    assert "OVERDUE" in text


def test_cli_exit_codes(tmp_path, capsys):
    assert main(["examples/devices.csv", "--as-of", "2026-11-19"]) == 1
    assert main([str(tmp_path / "none.csv")]) == 2
