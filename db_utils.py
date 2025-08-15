import typer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlite_models import Base
from tabulate import tabulate

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
    "mix": "segment_mix",
    "segmab": "segmented_mab_campaigns"
}

def get_table(name_or_alias):
    """Resolve alias or table name to SQLAlchemy model class."""
    table_name = TABLE_ALIASES.get(name_or_alias, name_or_alias)
    table_class = TABLES.get(table_name)
    if not table_class:
        raise typer.BadParameter(f"Unknown table or alias: {name_or_alias}")
    return table_class

@app.command()
def print(name_or_alias: str):
    """Pretty-print all rows in a table using tabulate."""
    table = get_table(name_or_alias)
    rows = session.query(table).all()

    if not rows:
        typer.echo(f"Table '{name_or_alias}' is empty.")
        return

    # Extract column names
    columns = [col.name for col in table.__table__.columns]

    # Build rows as list of dict values
    table_data = [[getattr(row, col) for col in columns] for row in rows]

    typer.echo(tabulate(table_data, headers=columns, tablefmt="grid"))

@app.command()
def clear(name_or_alias: str):
    """Delete all rows from a table."""
    table = get_table(name_or_alias)
    session.query(table).delete()
    session.commit()
    typer.echo(f"Cleared table: {name_or_alias}")

@app.command()
def insert(name_or_alias: str):
    """
    Insert a row into a table interactively using prompts for each column.
    """
    table = get_table(name_or_alias)
    col_values = {}

    for col in table.__table__.columns:
        if col.primary_key:
            continue  # skip auto-increment ID
        val = typer.prompt(f"Enter value for '{col.name}' (leave blank for NULL)", default="")
        if val == "":
            col_values[col.name] = None
        else:
            # Convert to the appropriate type
            if col.type.python_type == int:
                col_values[col.name] = int(val)
            elif col.type.python_type == float:
                col_values[col.name] = float(val)
            else:
                col_values[col.name] = val

    obj = table(**col_values)
    session.add(obj)
    session.commit()
    typer.echo(f"✅ Inserted row into '{name_or_alias}'")

if __name__ == "__main__":
    app()
