import pytest

@pytest.fixture(scope="function", autouse=True)
def test_db_session(monkeypatch):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from ml_liveops_dashboard.sqlite_models import Base
    from ml_liveops_dashboard import db_utils
    from ml_liveops_dashboard.db_utils import clear
    from constants import TESTS_DB_PATH

    # 1. Connect to local tests db
    engine = create_engine(TESTS_DB_PATH)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()

    # 2. Patch db_utils to use this session
    monkeypatch.setattr(db_utils, "session", session)

    db_utils.TABLES = {
        cls.__tablename__: cls
        for cls in Base.__subclasses__()  # iterate ORM classes
    }
    print("running test fixture")
    clear()
    yield session
    clear()

    # 4. Cleanup
    session.close()
