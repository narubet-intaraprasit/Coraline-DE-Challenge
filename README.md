# Coraline Challenge - solution

## Files
- `import_food_sales.py` - Task 1: reads the `FoodSales` sheet from
  `[For candidate] de_challenge_data.xlsx` and loads it into a PostgreSQL
  table `food_sales`.
- `create_cat_reg.sql` - Task 2: creates table `cat_reg` from `food_sales`
  (category x region pivot with a Grand Total row/column).
- `requirements.txt` - Python dependencies.

## Key detail found in the data
The `FoodSales` sheet is not one flat table - it actually contains **two
stacked blocks**, one for 2022 and one for 2023, each with its own small
year-label row and its own repeated header row, separated by a blank row
(2022 block: rows 1-124, 2023 block: rows 126-249 in the sheet). That is
exactly what the brief means by "รวมข้อมูลทุกปีไว้ใน table เดียวกัน" - the
script detects both blocks and concatenates them into one clean 244-row
table. (A naive `pandas.read_excel()` on the sheet as-is would silently
mangle the second block.)

## Setup

```bash
pip install -r requirements.txt
```

Have a PostgreSQL server reachable with:
- database: `challenge`
- user: `root`
- password: `DataEngineer_2024`
- table (task 1): `food_sales`

(Host/port weren't specified in the brief - default is `localhost:5432`;
override with `--host` / `--port` or `PGHOST` / `PGPORT` env vars.)

## Run

```bash
# Task 1 - import FoodSales (both years) into Postgres
python import_food_sales.py --excel "/path/to/[For candidate] de_challenge_data.xlsx"

# Task 2 - build cat_reg from food_sales
psql -h localhost -U root -d challenge -f create_cat_reg.sql
```

## Run with Docker

No local PostgreSQL needed - everything runs in containers.

```bash
docker compose up --build
```

This starts Postgres, waits for it to be healthy, then runs Task 1 (import) and Task 2
(`cat_reg` pivot) automatically, printing `cat_reg` at the end.

Check the result any time after it's up:

```bash
docker compose exec db psql -U root -d challenge -c "SELECT * FROM cat_reg;"
```

Tear down (including the data volume):

```bash
docker compose down -v
```

## Verified output of `cat_reg`

Tested end-to-end against a local PostgreSQL 16 instance; matches the
target table in the brief (values rounded to whole dollars there):

| category    | east     | west     | grand_total |
|-------------|---------:|---------:|------------:|
| Bars        |  6355.20 |  4180.37 |    10535.57 |
| Cookies     | 10683.50 |  6528.91 |    17212.41 |
| Crackers    |  3025.83 |   314.10 |     3339.93 |
| Snacks      |  1459.83 |   777.84 |     2237.67 |
| Grand Total | 21524.36 | 11801.22 |    33325.58 |
