#!/usr/bin/env bash
set -euo pipefail

echo "Waiting for PostgreSQL at $PGHOST:$PGPORT ..."
until pg_isready -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" >/dev/null 2>&1; do
  echo "  ...not ready yet, retrying in 2s"
  sleep 2
done
echo "PostgreSQL is ready."

echo "== Task 1: importing FoodSales into food_sales =="
python import_food_sales.py \
  --excel "/app/[For candidate] de_challenge_data.xlsx" \
  --host "$PGHOST" --port "$PGPORT" --dbname "$PGDATABASE" \
  --user "$PGUSER" --password "$PGPASSWORD"

echo "== Task 2: building cat_reg =="
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" -f create_cat_reg.sql

echo "== Verify: SELECT * FROM cat_reg =="
psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" -c "SELECT * FROM cat_reg;"
