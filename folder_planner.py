from datetime import date


def compute_default_year(today: date) -> int:
    if today.month == 12:
        return today.year + 1
    return today.year
