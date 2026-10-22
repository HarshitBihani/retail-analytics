-- 03_customers_rfm.sql : RFM segmentation (Recency, Frequency, Monetary) on identified customers.
-- Snapshot date = day after the last transaction.

CREATE OR REPLACE TABLE rfm_base AS
SELECT customer_id,
       DATE_DIFF('day', MAX(invoice_date), (SELECT MAX(invoice_date) + INTERVAL 1 DAY FROM sales)) AS recency_days,
       COUNT(DISTINCT invoice)   AS frequency,
       ROUND(SUM(revenue), 2)    AS monetary
FROM sales WHERE customer_id IS NOT NULL
GROUP BY customer_id;

-- Scores 1 (worst) to 5 (best). Ties are broken by customer_id so buckets stay balanced.
CREATE OR REPLACE TABLE rfm AS
SELECT *,
       6 - NTILE(5) OVER (ORDER BY recency_days, customer_id) AS r_score,
       NTILE(5) OVER (ORDER BY frequency, customer_id)        AS f_score,
       NTILE(5) OVER (ORDER BY monetary, customer_id)         AS m_score
FROM rfm_base;

CREATE OR REPLACE TABLE rfm_segments AS
SELECT *,
       CASE
         WHEN r_score >= 4 AND f_score >= 4 THEN 'Champions'
         WHEN r_score >= 3 AND f_score >= 3 THEN 'Loyal'
         WHEN r_score >= 4 AND f_score <= 2 THEN 'New / Promising'
         WHEN r_score <= 2 AND f_score >= 4 THEN 'At Risk (was valuable)'
         WHEN r_score <= 2 AND f_score >= 3 THEN 'Needs Attention'
         ELSE 'Lost / Low value'
       END AS segment
FROM rfm;

CREATE OR REPLACE TABLE segment_summary AS
SELECT segment,
       COUNT(*)                          AS customers,
       ROUND(SUM(monetary), 0)           AS revenue,
       ROUND(AVG(monetary), 0)           AS avg_revenue,
       ROUND(AVG(recency_days), 0)       AS avg_recency_days,
       ROUND(AVG(frequency), 1)          AS avg_orders
FROM rfm_segments GROUP BY segment ORDER BY revenue DESC;
