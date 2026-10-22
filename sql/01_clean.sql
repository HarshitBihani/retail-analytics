-- 01_clean.sql : turn the raw 1.07M-row export into trustworthy analysis tables.
-- Every rule is counted in cleaning_log so nothing is dropped silently.

CREATE OR REPLACE TABLE raw AS SELECT * FROM 'raw/online_retail_ii.parquet';

CREATE OR REPLACE TABLE cleaning_log AS
SELECT 'raw rows' AS step, COUNT(*) AS rows_affected FROM raw
UNION ALL SELECT 'cancellation invoices (start with C) -> moved to returns',
       COUNT(*) FROM raw WHERE invoice LIKE 'C%'
UNION ALL SELECT 'non-product codes (postage, fees, manual, samples, vouchers)',
       COUNT(*) FROM raw WHERE NOT regexp_matches(stock_code, '^[0-9]{5}')
UNION ALL SELECT 'zero or negative price (adjustments, write-offs)',
       COUNT(*) FROM raw WHERE price <= 0 AND invoice NOT LIKE 'C%'
UNION ALL SELECT 'zero or negative quantity (not cancellations)',
       COUNT(*) FROM raw WHERE quantity <= 0 AND invoice NOT LIKE 'C%'
UNION ALL SELECT 'rows with no customer id (kept for revenue, excluded from customer analysis)',
       COUNT(*) FROM raw WHERE customer_id IS NULL;

-- Orders placed and cancelled within a day for the exact same quantity (e.g. an 80,995-unit order
-- reversed 12 minutes later). They are not real demand and not real returns, so they are removed
-- from BOTH sides. Otherwise they inflate revenue and make two products look 100% returned.
CREATE OR REPLACE TABLE reversed AS
SELECT DISTINCT s.invoice AS sale_invoice, c.invoice AS return_invoice, s.stock_code
FROM raw s JOIN raw c
  ON  c.customer_id = s.customer_id
  AND c.stock_code  = s.stock_code
  AND c.quantity    = -s.quantity
  AND c.invoice LIKE 'C%' AND s.invoice NOT LIKE 'C%'
  AND c.invoice_date >= s.invoice_date
  AND c.invoice_date <= s.invoice_date + INTERVAL 1 DAY
WHERE s.quantity >= 1000;   -- only large lines: small same-day swaps are normal customer behaviour

INSERT INTO cleaning_log
SELECT 'large orders cancelled within 24h (removed from sales and returns)', COUNT(*) FROM reversed;

-- Valid product sales: real products, positive quantity and price, exact duplicate lines removed.
CREATE OR REPLACE TABLE sales AS
SELECT DISTINCT
    invoice, stock_code, description, quantity, invoice_date, price,
    CAST(customer_id AS BIGINT) AS customer_id, country,
    quantity * price AS revenue,
    DATE_TRUNC('month', invoice_date) AS month
FROM raw
WHERE invoice NOT LIKE 'C%'
  AND regexp_matches(stock_code, '^[0-9]{5}')
  AND quantity > 0
  AND price > 0
  AND NOT EXISTS (SELECT 1 FROM reversed r WHERE r.sale_invoice = raw.invoice AND r.stock_code = raw.stock_code);

INSERT INTO cleaning_log
SELECT 'exact duplicate lines removed',
       (SELECT COUNT(*) FROM raw WHERE invoice NOT LIKE 'C%' AND regexp_matches(stock_code, '^[0-9]{5}') AND quantity > 0 AND price > 0)
       - (SELECT COUNT(*) FROM reversed)
       - (SELECT COUNT(*) FROM sales);
INSERT INTO cleaning_log SELECT 'clean sales rows used for analysis', COUNT(*) FROM sales;

-- Customer returns (credit notes)
CREATE OR REPLACE TABLE returns AS
SELECT invoice, stock_code, description, ABS(quantity) AS quantity, invoice_date, price,
       CAST(customer_id AS BIGINT) AS customer_id, country,
       ABS(quantity) * price AS revenue_lost,
       DATE_TRUNC('month', invoice_date) AS month
FROM raw
WHERE invoice LIKE 'C%' AND regexp_matches(stock_code, '^[0-9]{5}') AND price > 0
  AND NOT EXISTS (SELECT 1 FROM reversed r WHERE r.return_invoice = raw.invoice AND r.stock_code = raw.stock_code);
