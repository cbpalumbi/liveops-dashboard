import typer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlite_models import Base
from tabulate import tabulate
import json

app = typer.Typer()

# --- DB setup ---
engine = create_engine("sqlite:///mab.db", echo=False)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

# --- Automatic table mapping ---
TABLES = {
    mapper.class_.__tablename__: mapper.class_
    for mapper in Base.registry.mappers
}

# --- Aliases for convenience ---
TABLE_ALIASES = {
    "imp": "impressions",
    "camp": "data_campaigns",
    "seg": "segments",
    "seg-mix": "segment_mixes",
    "seg-mab": "segmented_mab_campaigns",
    "seg-mix-entry": "segment_mix_entries"
}

def get_table(name_or_alias):
    """Resolve alias or table name to SQLAlchemy model class."""
    table_name = TABLE_ALIASES.get(name_or_alias, name_or_alias)
    table_class = TABLES.get(table_name)
    if not table_class:
        raise typer.BadParameter(f"Unknown table or alias: {name_or_alias}")
    return table_class

@app.command()
def print(name_or_alias: str = None):
    """Pretty-print all rows in a table using tabulate. If no table is specified, print all tables."""
    tables_to_print = [name_or_alias] if name_or_alias else list(TABLES.keys())

    for table_name in tables_to_print:
        try:
            table = get_table(table_name)
        except typer.BadParameter:
            typer.echo(f"Unknown table or alias: {table_name}")
            continue

        rows = session.query(table).all()
        typer.echo(f"\n=== Table: {table_name} ===")

        if not rows:
            typer.echo("Table empty.")
            continue

        columns = [col.name for col in table.__table__.columns]
        table_data = [[getattr(row, col) for col in columns] for row in rows]
        typer.echo(tabulate(table_data, headers=columns, tablefmt="grid"))

@app.command()
def clear(name_or_alias: str = None):
    """Delete all rows from a table. If no table is specified, clear all tables."""
    
    if name_or_alias:
        # Clear a specific table
        table = get_table(name_or_alias)
        session.query(table).delete()
        session.commit()
        typer.echo(f"Cleared table: {name_or_alias}")
    else:
        # Clear all tables
        for table_name, table_class in TABLES.items():
            session.query(table_class).delete()
            typer.echo(f"Cleared table: {table_name}")
        session.commit()
        typer.echo("All tables cleared.")


import json
from typing import Union

@app.command()
def insert(name_or_alias: str, col_values_json: Union[str, dict]):
    """
    Insert a row into a table.
    Accepts a JSON string (from CLI) or a Python dict (from Python script).
    """
    table = get_table(name_or_alias)

    # Convert input to dict if needed
    if isinstance(col_values_json, str):
        col_values = json.loads(col_values_json)
    else:
        col_values = col_values_json

    # Convert types automatically
    for col in table.__table__.columns:
        if col.primary_key:
            continue
        val = col_values.get(col.name)
        if val is not None:
            if col.type.python_type == int:
                col_values[col.name] = int(val)
            elif col.type.python_type == float:
                col_values[col.name] = float(val)
            else:
                col_values[col.name] = str(val)

    obj = table(**col_values)
    session.add(obj)
    session.commit()
    typer.echo(f"Inserted row into '{name_or_alias}'")


if __name__ == "__main__":
    app()
