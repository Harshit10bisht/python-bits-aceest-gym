import pytest

from fitness_core import WORKOUTS, workouts_for


def test_workouts_dict_covers_all_programs():
    assert set(WORKOUTS.keys()) == {"Fat Loss (FL)", "Muscle Gain (MG)", "Beginner (BG)"}
    for items in WORKOUTS.values():
        assert isinstance(items, list) and len(items) >= 1


def test_workouts_for_returns_copy():
    items = workouts_for("Fat Loss (FL)")
    items.append("MUTATION")
    assert "MUTATION" not in workouts_for("Fat Loss (FL)")


def test_workouts_for_unknown_raises():
    with pytest.raises(KeyError):
        workouts_for("Nope")


def test_get_all_workouts(client):
    r = client.get("/workouts")
    assert r.status_code == 200
    body = r.get_json()
    assert "Fat Loss (FL)" in body
    assert isinstance(body["Muscle Gain (MG)"], list)


def test_get_program_workouts(client):
    r = client.get("/workouts/Beginner (BG)")
    assert r.status_code == 200
    body = r.get_json()
    assert body["program"] == "Beginner (BG)"
    assert len(body["workouts"]) >= 1


def test_get_program_workouts_unknown(client):
    r = client.get("/workouts/Unknown")
    assert r.status_code == 404
