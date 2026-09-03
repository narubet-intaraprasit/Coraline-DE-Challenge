#!/usr/bin/env python3
"""
Coraline Challenge - Task 1
----------------------------
Reads the "FoodSales" sheet from the candidate Excel file and loads it into
a PostgreSQL table, combining every year's data into a single table.

Why the "combine all years" step is needed:
The FoodSales sheet actually contains TWO stacked blocks (one per year -
2022 and 2023), each with its own small "year label" row and its own
repeated header row, separated by a blank row. A naive
`pandas.read_excel()` would treat the second block as garbage rows. This
script detects and skips those year-label / blank / repeated-header rows
and concatenates both blocks into one clean DataFrame before loading it.

Database target (per challenge spec):
    database_name : challenge
    user          : root
    password      : DataEngineer_2024
    table         : food_sales

Usage:
    python import_food_sales.py --excel "/path/to/de_challenge_data.xlsx"

Connection settings can be overridden with env vars / CLI flags (host and
port default to localhost:5432, since the challenge did not specify them).
"""
import argparse
import os
import sys

import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values

SHEET_NAME = "FoodSales"
TABLE_NAME = "food_sales"

EXPECTED_COLUMNS = [
    "ID", "Date", "Region", "City", "Category", "Product",
    "Qty", "UnitPrice", "TotalPrice",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--excel", required=True,
        help="Path to the '[For candidate] de_challenge_data.xlsx' file",
    )
    parser.add_argument("--sheet", default=SHEET_NAME, help="Sheet name to read")
    parser.add_argument("--host", default=os.getenv("PGHOST", "localhost"))
    parser.add_argument("--port", default=os.getenv("PGPORT", "5432"))
    parser.add_argument("--dbname", default=os.getenv("PGDATABASE", "challenge"))
    parser.add_argument("--user", default=os.getenv("PGUSER", "root"))
    parser.add_argument(
        "--password", default=os.getenv("PGPASSWORD", "DataEngineer_2024"),
    )
    parser.add_argument(
        "--table", default=TABLE_NAME, help="Destination table name",
    )
    return parser.parse_args()


def load_food_sales(excel_path: str, sheet_name: str) -> pd.DataFrame:
    """Read the FoodSales sheet and combine every stacked year block.

    Each block looks like:
        <year>, None, None, ...        <- year label row (skip)
        ID, Date, Region, ...          <- repeated header row (skip)
        <data rows...>
    blocks are separated by a fully-empty row.
    """
    raw = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)

    blocks = []
    current_rows = []

    def flush_block():
        if current_rows:
            block_df = pd.DataFrame(current_rows, columns=EXPECTED_COLUMNS)
            blocks.append(block_df)
            current_rows.clear()

    for _, row in raw.iterrows():
        values = row.tolist()
        first_cell = values[0]

        is_blank_row = all(pd.isna(v) for v in values)
        is_year_label_row = (
            not is_blank_row
            and all(pd.isna(v) for v in values[1:])
            and str(first_cell).strip().isdigit()
        )
        is_header_row = first_cell == "ID"

        if is_blank_row:
            flush_block()
            continue
        if is_year_label_row or is_header_row:
            continue

        current_rows.append(values)

    flush_block()

    if not blocks:
        raise ValueError(
            f"No data rows found in sheet '{sheet_name}' - check the file/sheet name."
        )

    df = pd.concat(blocks, ignore_index=True)

    # Normalize dtypes / column names for loading into Postgres.
    df["Date"] = pd.to_datetime(df["Date"])
    df.attrs["year_count"] = df["Date"].dt.year.nunique()
    df["Date"] = df["Date"].dt.date
    df["Qty"] = df["Qty"].astype(int)
    df["UnitPrice"] = df["UnitPrice"].astype(float)
    df["TotalPrice"] = df["TotalPrice"].astype(float)

    df.columns = [
        "id", "date", "region", "city", "category", "product",
        "qty", "unit_price", "total_price",
    ]
    return df


def load_to_postgres(df: pd.DataFrame, conn_params: dict, table_name: str) -> None:
    conn = psycopg2.connect(**conn_params)
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                sql.SQL("DROP TABLE IF EXISTS {table};").format(
                    table=sql.Identifier(table_name)
                )
            )
            cur.execute(
                sql.SQL(
                    """
                    CREATE TABLE {table} (
                        id          TEXT PRIMARY KEY,
                        date        DATE NOT NULL,
                        region      TEXT NOT NULL,
                        city        TEXT NOT NULL,
                        category    TEXT NOT NULL,
                        product     TEXT NOT NULL,
                        qty         INTEGER NOT NULL,
                        unit_price  NUMERIC(10, 2) NOT NULL,
                        total_price NUMERIC(12, 2) NOT NULL
                    );
                    """
                ).format(table=sql.Identifier(table_name))
            )

            records = list(df.itertuples(index=False, name=None))
            insert_stmt = sql.SQL(
                "INSERT INTO {table} "
                "(id, date, region, city, category, product, qty, unit_price, total_price) "
                "VALUES %s"
            ).format(table=sql.Identifier(table_name))
            execute_values(cur, insert_stmt.as_string(conn), records)
        print(f"Loaded {len(records)} rows into '{table_name}'.")
    finally:
        conn.close()


def main() -> None:
    args = parse_args()

    if not os.path.exists(args.excel):
        print(f"Excel file not found: {args.excel}", file=sys.stderr)
        sys.exit(1)

    df = load_food_sales(args.excel, args.sheet)
    print(f"Combined {df.attrs.get('year_count', '?')} year(s) of data -> {len(df)} rows total.")

    conn_params = dict(
        host=args.host, port=args.port, dbname=args.dbname,
        user=args.user, password=args.password,
    )
    load_to_postgres(df, conn_params, args.table)


if __name__ == "__main__":
    main()
