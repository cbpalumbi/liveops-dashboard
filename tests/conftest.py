import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers

from ml_liveops_dashboard.sqlite_models import Base
from ml_liveops_dashboard import db_utils

@pytest.fixture(scope="function")
def test_db_session(monkeypatch):
    
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()

    # modifies which db to use at runtime
    monkeypatch.setattr(db_utils, "session", session)

    yield session

    session.close()
    clear_mappers()
