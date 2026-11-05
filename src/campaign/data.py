"""Load the campaign data through the SQL layer in sql/."""

from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SQL_FILES = ["01_staging.sql", "02_data_quality.sql", "03_conversion_analysis.sql"]


def connect() -> duckdb.DuckDBPyConnection:
    """In-memory DuckDB with all views from sql/ created."""
    con = duckdb.connect()
    con.execute(f"set file_search_path = '{ROOT}'")
    for name in SQL_FILES:
        con.execute((ROOT / "sql" / name).read_text())
    return con


def load_calls(con: duckdb.DuckDBPyConnection | None = None) -> pd.DataFrame:
    con = con or connect()
    return con.sql("select * from stg_calls_dated order by call_id").df()


def view(name: str, con: duckdb.DuckDBPyConnection | None = None) -> pd.DataFrame:
    con = con or connect()
    return con.sql(f"select * from {name}").df()
