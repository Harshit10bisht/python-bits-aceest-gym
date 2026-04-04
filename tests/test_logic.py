from datetime import datetime

import pytest

from fitness_core import PROGRAMS, compute_calories, progress_week_label


def test_program_names_and_factors_match_baseline():
    assert PROGRAMS["Fat Loss (FL)"]["factor"] == 22
    assert PROGRAMS["Muscle Gain (MG)"]["factor"] == 35
    assert PROGRAMS["Beginner (BG)"]["factor"] == 26


@pytest.mark.parametrize(
    "program, weight, expected",
    [
        ("Fat Loss (FL)", 70.0, 1540),
        ("Muscle Gain (MG)", 80.0, 2800),
        ("Beginner (BG)", 60.0, 1560),
    ],
)
def test_compute_calories(program, weight, expected):
    assert compute_calories(weight, program) == expected


def test_compute_calories_unknown_program():
    with pytest.raises(KeyError):
        compute_calories(70.0, "Invalid")


def test_progress_week_label_format():
    fixed = datetime(2026, 4, 15, 12, 0, 0)
    label = progress_week_label(fixed)
    assert label.startswith("Week ")
    assert "2026" in label
