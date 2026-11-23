import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src import models  # noqa: F401  (registers Task on Base.metadata)
from src.database import Base, get_db
from src.main import app


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    # Deliberately not used as a context manager: entering it would run the
    # production lifespan and create src/tasks.db.
    yield TestClient(app)
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture
def make_task(client):
    def _make(title="Write tests", description="Cover the API", **extra):
        response = client.post(
            "/tasks", json={"title": title, "description": description, **extra}
        )
        assert response.status_code == 201, response.text
        return response.json()

    return _make
