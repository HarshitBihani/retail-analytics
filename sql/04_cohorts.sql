-- 04_cohorts.sql : of the customers who first bought in month X, how many still buy N months later?

CREATE OR REPLACE TABLE cohort_activity AS
WITH first_buy AS (
  SELECT customer_id, MIN(month) AS cohort_month
  FROM sales WHERE customer_id IS NOT NULL GROUP BY customer_id
)
SELECT f.cohort_month,
       DATE_DIFF('month', f.cohort_month, s.month) AS months_since,
       COUNT(DISTINCT s.customer_id) AS active_customers
FROM sales s JOIN first_buy f USING (customer_id)
WHERE s.customer_id IS NOT NULL
GROUP BY 1, 2;

CREATE OR REPLACE TABLE cohort_retention AS
SELECT a.cohort_month, a.months_since,
       a.active_customers,
       ROUND(100.0 * a.active_customers / c0.active_customers, 1) AS retention_pct
FROM cohort_activity a
JOIN cohort_activity c0 ON c0.cohort_month = a.cohort_month AND c0.months_since = 0
WHERE a.cohort_month < DATE '2011-12-01'
ORDER BY 1, 2;
