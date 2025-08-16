# db_utils.py
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

# ------------------------
# PRINT COMMAND
# ------------------------
@app.command()
def print(
    name_or_alias: str = typer.Argument(
        None,
        help="Table name or alias. Leave empty to print all tables."
    )
):
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

# ------------------------
# CLEAR COMMAND
# ------------------------
@app.command()
def clear(
    name_or_alias: str = typer.Argument(
        None,
        help="Table name or alias. Leave empty to clear all tables."
    )
):
    """Delete all rows from a table. If no table is specified, clear all tables."""
    if name_or_alias:
        table = get_table(name_or_alias)
        session.query(table).delete()
        session.commit()
        typer.echo(f"Cleared table: {name_or_alias}")
    else:
        for table_name, table_class in TABLES.items():
            session.query(table_class).delete()
            typer.echo(f"Cleared table: {table_name}")
        session.commit()
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
    )
):
    """
    Insert a row into a table.
    - CLI: pass a JSON string for col_values_json
    - Python: pass a dict directly
    """
    table = get_table(name_or_alias)

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
            else:
                col_values[col.name] = str(val)

    obj = table(**col_values)
    session.add(obj)
    session.commit()
    typer.echo(f"Inserted row into '{name_or_alias}'")

# ------------------------
# ENTRY POINT
# ------------------------
if __name__ == "__main__":
    app()
