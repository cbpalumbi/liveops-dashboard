import json
import pytest
from ml_liveops_dashboard import db_utils
from click.testing import CliRunner
import typer

runner = CliRunner()

# ---------- get_table ----------
def test_get_table_valid_name(monkeypatch):
    # Pick first table name from registry
    name = next(iter(db_utils.TABLES.keys()))
    assert db_utils.get_table(name) == db_utils.TABLES[name]

def test_get_table_valid_alias():
    alias = next(iter(db_utils.TABLE_ALIASES.keys()))
    resolved = db_utils.get_table(alias)
    assert resolved == db_utils.TABLES[db_utils.TABLE_ALIASES[alias]]

def test_get_table_invalid():
    with pytest.raises(typer.BadParameter):
        db_utils.get_table("does_not_exist")

# ---------- insert ----------
def test_insert_with_json(test_db_session):
    result = runner.invoke(db_utils.app, [
        "insert", "data_campaigns", json.dumps({
            "name": "From JSON",
            "campaign_type": "mab",
            "banner_id": 123
        })
    ])
    assert result.exit_code == 0
    assert "Inserted row" in result.stdout

def test_insert_with_dict(test_db_session):
    # Direct Python call instead of CLI
    db_utils.insert("data_campaigns", {
        "name": "From Dict",
        "campaign_type": "mab",
        "banner_id": 456
    })
    rows = test_db_session.query(db_utils.TABLES["data_campaigns"]).all()
    assert any(r.name == "From Dict" for r in rows)

def test_insert_with_type_conversion(test_db_session):
    db_utils.insert("data_campaigns", {
        "name": "With Types",
        "campaign_type": "mab",
        "banner_id": "789"  # should cast to int
    })
    row = test_db_session.query(db_utils.TABLES["data_campaigns"]).filter_by(name="With Types").first()
    assert isinstance(row.banner_id, int)

def test_insert_interactive(monkeypatch, test_db_session):
    # Monkeypatch typer.prompt to simulate input
    monkeypatch.setattr("typer.prompt", lambda *_, **__: "InteractiveName")
    result = runner.invoke(db_utils.app, ["insert", "data_campaigns"])
    assert "Inserted row" in result.stdout

# ---------- print ----------
def test_print_empty_table(test_db_session):
    result = runner.invoke(db_utils.app, ["print", "data_campaigns"])
    assert "Table empty." in result.stdout

def test_print_all_tables(test_db_session):
    result = runner.invoke(db_utils.app, ["print"])
    assert "Table:" in result.stdout

def test_print_with_unknown_table(test_db_session):
    result = runner.invoke(db_utils.app, ["print", "does_not_exist"])
    assert "Unknown table" in result.stdout

# ---------- clear ----------
def test_clear_specific_table(test_db_session):
    # Insert row
    db_utils.insert("data_campaigns", {"name": "ToDelete", "campaign_type": "mab", "banner_id": 1})
    result = runner.invoke(db_utils.app, ["clear", "data_campaigns"])
    assert "Cleared table" in result.stdout
    rows = test_db_session.query(db_utils.TABLES["data_campaigns"]).all()
    assert len(rows) == 0

def test_clear_all_tables(test_db_session):
    db_utils.insert("data_campaigns", {"name": "ToDeleteAll", "campaign_type": "mab", "banner_id": 2})
    result = runner.invoke(db_utils.app, ["clear"])
    assert "All tables cleared." in result.stdout

def test_clear_impressions_with_campaign_id(test_db_session):
    # Insert fake impression row
    Impressions = db_utils.TABLES["impressions"]
    imp = Impressions(data_campaign_id=42, variant_id=1, clicked=1)
    test_db_session.add(imp)
    test_db_session.commit()

    result = runner.invoke(db_utils.app, ["clear", "impressions", "42"])
    assert "Cleared 1 rows" in result.stdout
    rows = test_db_session.query(Impressions).all()
    assert len(rows) == 0
