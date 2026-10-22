-- 02_trends.sql : monthly revenue, orders, customers, with UK vs international split.
-- Dec 2011 is excluded: the data stops on 9 Dec 2011, so that month is incomplete.

CREATE OR REPLACE TABLE monthly AS
SELECT month,
       ROUND(SUM(revenue), 0)                                         AS revenue,
       COUNT(DISTINCT invoice)                                        AS orders,
       COUNT(DISTINCT customer_id)                                    AS customers,
       ROUND(SUM(revenue) / COUNT(DISTINCT invoice), 2)               AS avg_order_value,
       ROUND(SUM(CASE WHEN country = 'United Kingdom' THEN revenue END), 0) AS uk_revenue,
       ROUND(SUM(CASE WHEN country <> 'United Kingdom' THEN revenue END), 0) AS intl_revenue
FROM sales
WHERE month < DATE '2011-12-01'
GROUP BY month ORDER BY month;

CREATE OR REPLACE TABLE country_rev AS
SELECT country, ROUND(SUM(revenue), 0) AS revenue, COUNT(DISTINCT customer_id) AS customers,
       COUNT(DISTINCT invoice) AS orders
FROM sales GROUP BY country ORDER BY revenue DESC;

CREATE OR REPLACE TABLE top_products AS
SELECT stock_code, ANY_VALUE(description) AS description,
       ROUND(SUM(revenue), 0) AS revenue, SUM(quantity) AS units,
       COUNT(DISTINCT customer_id) AS customers
FROM sales GROUP BY stock_code ORDER BY revenue DESC LIMIT 25;
