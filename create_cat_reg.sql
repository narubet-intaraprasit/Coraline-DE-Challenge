-- Coraline Challenge - Task 2
-- ----------------------------
-- Creates table `cat_reg` from `food_sales` (built by import_food_sales.py
-- in Task 1): total price per category, pivoted by region (East / West),
-- with a Grand Total column and a Grand Total row - matching the shape:
--
--   Category  | East   | West   | Grand Total
--   Bars      | 6,355  | 4,180  | 10,536
--   Cookies   | 10,684 | 6,529  | 17,212
--   Crackers  | 3,026  | 314    | 3,340
--   Snacks    | 1,460  | 778    | 2,238
--
-- Run after Task 1's import script has populated food_sales, e.g.:
--   psql -h localhost -U root -d challenge -f create_cat_reg.sql

DROP TABLE IF EXISTS cat_reg;

CREATE TABLE cat_reg AS
WITH by_category AS (
    SELECT
        category,
        SUM(total_price) FILTER (WHERE region = 'East') AS east,
        SUM(total_price) FILTER (WHERE region = 'West') AS west,
        SUM(total_price)                                AS grand_total
    FROM food_sales
    GROUP BY category
),
grand_total_row AS (
    SELECT
        'Grand Total' AS category,
        SUM(east)        AS east,
        SUM(west)        AS west,
        SUM(grand_total) AS grand_total
    FROM by_category
)
SELECT category, east, west, grand_total, 0 AS sort_order FROM by_category
UNION ALL
SELECT category, east, west, grand_total, 1 AS sort_order FROM grand_total_row
ORDER BY sort_order, category;

ALTER TABLE cat_reg DROP COLUMN sort_order;

-- Sanity check
SELECT * FROM cat_reg;
