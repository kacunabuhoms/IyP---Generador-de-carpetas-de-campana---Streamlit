from datetime import date

from folder_planner import compute_default_year


def test_compute_default_year_same_year_when_no_rollover():
    assert compute_default_year(date(2026, 8, 15)) == 2026


def test_compute_default_year_rolls_over_in_december():
    assert compute_default_year(date(2026, 12, 1)) == 2027


def test_compute_default_year_january_stays_same_year():
    assert compute_default_year(date(2026, 1, 5)) == 2026
