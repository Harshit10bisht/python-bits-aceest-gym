def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


def test_programs(client):
    r = client.get("/programs")
    assert r.status_code == 200
    data = r.get_json()
    names = {p["name"] for p in data}
    assert "Fat Loss (FL)" in names
    assert "Muscle Gain (MG)" in names
    assert "Beginner (BG)" in names


def test_create_client_and_get(client):
    body = {
        "name": "Alex",
        "age": 28,
        "weight": 75.0,
        "program": "Fat Loss (FL)",
    }
    r = client.post("/clients", json=body)
    assert r.status_code == 201
    j = r.get_json()
    assert j["calories"] == 1650

    g = client.get("/clients/Alex")
    assert g.status_code == 200
    assert g.get_json()["program"] == "Fat Loss (FL)"


def test_create_client_missing_name_or_program(client):
    r = client.post("/clients", json={"name": "", "program": "Beginner (BG)"})
    assert r.status_code == 400
    r = client.post("/clients", json={"name": "Bob", "program": ""})
    assert r.status_code == 400


def test_create_client_unknown_program(client):
    r = client.post(
        "/clients",
        json={"name": "Bob", "age": 30, "weight": 70, "program": "Unknown"},
    )
    assert r.status_code == 400


def test_get_client_not_found(client):
    r = client.get("/clients/nobody")
    assert r.status_code == 404


def test_save_progress(client):
    client.post(
        "/clients",
        json={
            "name": "Casey",
            "age": 32,
            "weight": 68.0,
            "program": "Beginner (BG)",
        },
    )
    r = client.post("/clients/Casey/progress", json={"adherence": 85})
    assert r.status_code == 201
    j = r.get_json()
    assert j["client_name"] == "Casey"
    assert j["adherence"] == 85
    assert "week" in j


def test_save_progress_adherence_validation(client):
    client.post(
        "/clients",
        json={"name": "Dana", "age": 25, "weight": 60, "program": "Fat Loss (FL)"},
    )
    assert client.post("/clients/Dana/progress", json={"adherence": 101}).status_code == 400
    assert client.post("/clients/Dana/progress", json={"adherence": -1}).status_code == 400
