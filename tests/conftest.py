import pytest

from app import create_app


@pytest.fixture
def client(tmp_path):
    db_path = tmp_path / "test.db"
    app = create_app(str(db_path))
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c
