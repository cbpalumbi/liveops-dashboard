import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers
from sqlite_models import Base
import db_utils

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
