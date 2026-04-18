import os


def test_version_default(client):
    r = client.get("/version")
    assert r.status_code == 200
    assert r.get_json() == {"version": "v2"}


def test_version_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("APP_VERSION", "v2")
    from app import create_app

    app = create_app(str(tmp_path / "v.db"))
    with app.test_client() as c:
        r = c.get("/version")
        assert r.status_code == 200
        assert r.get_json() == {"version": "v2"}
    if "APP_VERSION" in os.environ:
        monkeypatch.delenv("APP_VERSION", raising=False)
