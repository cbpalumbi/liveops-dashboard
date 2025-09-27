# db_utils.py
import typer
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from tabulate import tabulate
import json
import datetime

from ml_liveops_dashboard.sqlite_models import Base
from constants import DB_PATH 

app = typer.Typer()

engine = create_engine(DB_PATH, echo=False)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

# --- Automatic table mapping ---
TABLES = {
    cls.__tablename__: cls
    for cls in Base.__subclasses__()  # iterate ORM classes
}

# --- Aliases for convenience ---
TABLE_ALIASES = {
    "imp": "impressions",
    "camp": "data_campaigns",
    "seg": "segments",
    "seg-mix": "segment_mixes",
    "seg-mix-entry": "segment_mix_entries"
}

def get_table(name_or_alias):
    # If Typer passed an ArgumentInfo, extract the name
    if not isinstance(name_or_alias, str):
        if hasattr(name_or_alias, "name"):
            name_or_alias = name_or_alias.name
        else:
            raise ValueError(f"Table name must be a string, got {type(name_or_alias)}")

    name_or_alias_lower = name_or_alias.lower()

    if name_or_alias_lower in TABLES:
        return TABLES[name_or_alias_lower]
    if name_or_alias_lower in TABLE_ALIASES:
        return TABLES[TABLE_ALIASES[name_or_alias_lower]]

    raise ValueError(f"Unknown table or alias: {name_or_alias}")



# ------------------------
# PRINT COMMAND
# ------------------------
@app.command()
def print(
    name_or_alias = typer.Argument(
        None,
        help="Table name or alias. Leave empty to print all tables."
    ),
    db=None  # optional session override for pytest
):
    """Pretty-print all rows in a table using tabulate. 
    If no table is specified, print all tables."""
    
    session_to_use = db or session

    # Handle Typer ArgumentInfo objects
    if name_or_alias is not None and not isinstance(name_or_alias, str):
        if hasattr(name_or_alias, "name"):
            name_or_alias = name_or_alias.name
        else:
            raise ValueError(f"Table name must be a string, got {type(name_or_alias)}")

    tables_to_print = [name_or_alias] if name_or_alias else list(TABLES.keys())

    for table_name in tables_to_print:

        table = get_table(table_name)

        # Check if table actually exists in the DB
        if not inspect(session_to_use.bind).has_table(table.__tablename__):
            typer.echo(f"Table '{table_name}' does not exist in the database.")
            continue

        rows = session_to_use.query(table).all()
        typer.echo(f"\n=== Table: {table_name} ===")

        if not rows:
            typer.echo("Table empty.")
            continue

        columns = [col.name for col in table.__table__.columns]
        table_data = [[getattr(row, col) for col in columns] for row in rows]
        typer.echo(tabulate(table_data, headers=columns, tablefmt="grid"))


# ------------------------
# CLEAR COMMAND
# ------------------------
@app.command()
def clear(
    name_or_alias = typer.Argument(
        None,
        help="Table name or alias. Leave empty to clear all tables."
    ),
    data_campaign_id: int = typer.Argument(
        None,
        help="If clearing impressions, only delete rows for this data campaign ID."
    ),
    db=None  # optional session override for pytest
):
    from typer.models import ArgumentInfo
    """Delete rows from a table, or all tables if none specified."""
    session_to_use = db or session

    # Normalize name_or_alias: Typer passes ArgumentInfo if called directly
    if name_or_alias is None or isinstance(name_or_alias, ArgumentInfo):
        tables_to_clear = list(TABLES.keys())
    else:
        tables_to_clear = [name_or_alias]
    # Normalize data_campaign_id
    if isinstance(data_campaign_id, ArgumentInfo):
        data_campaign_id = None

    for table_name in tables_to_clear:
        try:
            table = get_table(table_name)
        except ValueError:
            typer.echo(f"Unknown table or alias: {table_name}")
            continue

        # Check if table actually exists in the DB
        if not inspect(session_to_use.bind).has_table(table.__tablename__):
            typer.echo(f"Table '{table_name}' does not exist in the database.")
            continue

        if table_name in ("imp", "impressions") and data_campaign_id is not None:
            deleted = session_to_use.query(table).filter(
                table.data_campaign_id == data_campaign_id
            ).delete()
            session_to_use.commit()
            typer.echo(f"Cleared {deleted} rows from {table_name} for data_campaign_id={data_campaign_id}")
        else:
            session_to_use.query(table).delete()
            session_to_use.commit()
            typer.echo(f"Cleared table: {table_name}")

    if name_or_alias is None:
        typer.echo("All tables cleared.")



# ------------------------
# INSERT COMMAND
# ------------------------
@app.command()
def insert(
    name_or_alias: str = typer.Argument(..., help="Table name or alias."),
    col_values_json: str = typer.Argument(
        None,
        help="JSON string of column values. Leave empty for interactive input."
    ),
    db=None # optional session override for pytest
):
    """
    Insert a row into a table.
    - CLI: pass a JSON string for col_values_json
    - Python: pass a dict directly
    """
    table = get_table(name_or_alias)
    session_to_use = db or session

    # --- Check that the table exists in the DB ---
    if not inspect(session_to_use.bind).has_table(table.__tablename__):
        typer.echo(f"Error: Table '{name_or_alias}' does not exist in the database.")
        raise ValueError(f"Table '{name_or_alias}' does not exist in the database.")

    # Detect if called from Python with dict
    if isinstance(col_values_json, dict):
        col_values = col_values_json
    elif isinstance(col_values_json, str) and col_values_json:
        col_values = json.loads(col_values_json)
    else:
        # Interactive mode if no input provided
        col_values = {}
        for col in table.__table__.columns:
            if col.primary_key:
                continue
            val = typer.prompt(f"Enter value for '{col.name}' (leave blank for NULL)", default="")
            col_values[col.name] = None if val == "" else val

    # Type conversion
    for col in table.__table__.columns:
        if col.primary_key:
            continue
        val = col_values.get(col.name)
        if val is not None:
            if col.type.python_type == int:
                col_values[col.name] = int(val)
            elif col.type.python_type == float:
                col_values[col.name] = float(val)
            elif col.type.python_type == datetime.datetime:
                try:
                    col_values[col.name] = datetime.datetime.fromisoformat(str(val))
                except ValueError:
                    raise ValueError(f"Invalid datetime format for column '{col.name}'. Received: {val}")
            else:
                col_values[col.name] = str(val)

    obj = table(**col_values)
    session_to_use.add(obj)
    session_to_use.commit()
    typer.echo(f"Inserted row into '{name_or_alias}'")

# ------------------------
# ENTRY POINT
# ------------------------
if __name__ == "__main__":
    app()
