import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers

from ml_liveops_dashboard.sqlite_models import Base
from ml_liveops_dashboard import db_utils

@pytest.fixture(scope="function")
def test_db_session(monkeypatch):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker, clear_mappers
    from ml_liveops_dashboard.sqlite_models import Base
    from ml_liveops_dashboard import db_utils

    # 1. Create fresh in-memory DB
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()

    # 2. Patch db_utils to use this session
    monkeypatch.setattr(db_utils, "session", session)

    # 3. Rebuild TABLES so ORM classes point to correct mappers
    db_utils.TABLES = {mapper.class_.__tablename__: mapper.class_ for mapper in Base.registry.mappers}

    yield session

    # 4. Cleanup
    session.close()
    clear_mappers()
