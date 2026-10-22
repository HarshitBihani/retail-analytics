-- 05_returns_and_baskets.sql : where money leaks (returns) and what to bundle (baskets).

CREATE OR REPLACE TABLE returns_by_product AS
WITH sold AS (
  SELECT stock_code, ANY_VALUE(description) AS description, SUM(quantity) AS units_sold, SUM(revenue) AS revenue
  FROM sales GROUP BY stock_code
), ret AS (
  SELECT stock_code, SUM(quantity) AS units_returned, SUM(revenue_lost) AS revenue_lost, COUNT(*) AS return_lines
  FROM returns GROUP BY stock_code
)
SELECT s.stock_code, s.description, s.units_sold, r.units_returned,
       ROUND(100.0 * r.units_returned / s.units_sold, 1) AS return_rate_pct,
       ROUND(r.revenue_lost, 0) AS revenue_lost
FROM sold s JOIN ret r USING (stock_code)
WHERE s.units_sold >= 500                -- ignore tiny-volume noise
ORDER BY r.revenue_lost DESC;

-- Products most often bought together (top 300 products by orders, pairs seen in 150+ baskets)
CREATE OR REPLACE TABLE basket_pairs AS
WITH popular AS (
  SELECT stock_code FROM sales GROUP BY stock_code ORDER BY COUNT(DISTINCT invoice) DESC LIMIT 300
), lines AS (
  SELECT DISTINCT s.invoice, s.stock_code, s.description
  FROM sales s JOIN popular USING (stock_code)
)
SELECT a.description AS product_a, b.description AS product_b, COUNT(*) AS baskets_together
FROM lines a JOIN lines b ON a.invoice = b.invoice AND a.stock_code < b.stock_code
GROUP BY 1, 2
HAVING COUNT(*) >= 150
ORDER BY baskets_together DESC
LIMIT 15;
