import pytest
from click.testing import CliRunner
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, configure_mappers
from ml_liveops_dashboard import db_utils
from ml_liveops_dashboard.sqlite_models import Base, DataCampaign, Impression

runner = CliRunner()

# ---------- Fixture ----------
@pytest.fixture(scope="function")
def test_db_session(monkeypatch):
    # 1. Ensure mappers are configured
    configure_mappers()

    # 2. Create fresh in-memory DB
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()

    # 3. Patch db_utils to use this session and rebuild TABLES
    monkeypatch.setattr(db_utils, "session", session)
    db_utils.TABLES = {mapper.class_.__tablename__: mapper.class_ for mapper in Base.registry.mappers}

    yield session

    # 4. Cleanup
    session.close()


# ---------- get_table ----------
def test_get_table_valid_name():
    name = next(iter(db_utils.TABLES.keys()))
    table_class = db_utils.get_table(name)
    assert table_class == db_utils.TABLES[name]


def test_get_table_valid_alias():
    alias = next(iter(db_utils.TABLE_ALIASES.keys()))
    table_class = db_utils.get_table(alias)
    assert table_class == db_utils.TABLES[db_utils.TABLE_ALIASES[alias]]


def test_get_table_invalid():
    with pytest.raises(ValueError):
        db_utils.get_table("does_not_exist")


# ---------- insert ----------
def test_insert_with_json(test_db_session):
    data = {
        "static_campaign_id": 1,
        "banner_id": 123,
        "campaign_type": "MAB",
        "segmented_mab_id": None
    }
    db_utils.insert("data_campaigns", data, db=test_db_session)

    table_class = db_utils.get_table("data_campaigns")
    row = test_db_session.query(table_class).first()
    assert row is not None
    assert row.static_campaign_id == 1
    assert row.banner_id == 123
    assert row.campaign_type == "MAB"
    assert row.segmented_mab_id is None


def test_insert_with_type_conversion(test_db_session):
    data = {
        "static_campaign_id": 2,
        "banner_id": "789",  # should cast to int
        "campaign_type": "MAB",
        "segmented_mab_id": None
    }
    db_utils.insert("data_campaigns", data, db=test_db_session)
    row = test_db_session.query(DataCampaign).filter_by(static_campaign_id=2).first()
    assert isinstance(row.banner_id, int)


# ---------- print ----------
def test_print_empty_table(test_db_session):
    db_utils.print("data_campaigns", db=test_db_session)


def test_print_all_tables(test_db_session):
    db_utils.print(name_or_alias=None, db=test_db_session)


def test_print_with_unknown_table(test_db_session):
    with pytest.raises(ValueError):
        db_utils.print("does_not_exist", db=test_db_session)


# ---------- clear ----------
def test_clear_specific_table(test_db_session):
    data = {
        "static_campaign_id": 3,
        "banner_id": 1,
        "campaign_type": "MAB",
        "segmented_mab_id": None
    }
    db_utils.insert("data_campaigns", data, db=test_db_session)
    db_utils.clear("data_campaigns", db=test_db_session)

    table_class = db_utils.get_table("data_campaigns")
    rows = test_db_session.query(table_class).all()
    assert len(rows) == 0


def test_clear_all_tables(test_db_session):
    data = {
        "static_campaign_id": 4,
        "banner_id": 2,
        "campaign_type": "MAB",
        "segmented_mab_id": None
    }
    db_utils.insert("data_campaigns", data, db=test_db_session)
    db_utils.clear(db=test_db_session)  # clear all tables

    table_class = db_utils.get_table("data_campaigns")
    rows = test_db_session.query(table_class).all()
    assert len(rows) == 0


def test_clear_impressions_with_campaign_id(test_db_session):
    imp = Impression(
        data_campaign_id=42,
        banner_id=1,
        variant_id=1,
        clicked=1,
        segment=None
    )
    test_db_session.add(imp)
    test_db_session.commit()

    db_utils.clear("impressions", "42", db=test_db_session)

    table_class = db_utils.get_table("impressions")
    rows = test_db_session.query(table_class).all()
    assert len(rows) == 0
