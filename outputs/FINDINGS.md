# Findings: Retail Analytics Decision Report

Data: UCI Online Retail II, a UK online gift retailer, 1 Dec 2009 to 9 Dec 2011, 1,067,371 raw rows.
All figures are computed by `build_report.py` from the SQL tables. Nothing here is typed by hand.

## The business in numbers
- Net revenue analysed: GBP 19,392,174 across 39,514 orders and 5,852 identified customers.
- 13.3% of revenue is guest checkout (no customer id). It counts in revenue, not in customer analysis.
- UK share of revenue: 85.3%.

## What I would tell the owner to do
1. **Protect the Champions.** 1,464 customers (25.0% of customers) bring 70.0% of revenue, averaging GBP 8,044 each.
2. **Win back At-Risk customers.** 359 customers who spent GBP 1,036,347 in total have been silent for about 343 days. If 10 to 20% return at half their old yearly spend: about GBP 25,909 to GBP 51,817 a year (assumption-based planning range, not a forecast).
3. **Fix repeat purchase.** 21% of new customers buy again in month 1; 18% are still buying 12 months later. 27.7% of customers bought only once. A 5-point lift in month-1 return is about 11 extra repeat buyers a month (about GBP 7,986 a month).
4. **Plan for September.** Sep to Nov was 36.2% of 2010 revenue; November ran 2.2x the off-peak average.
5. **Sell bundles.** Colour and size variants are bought in the same basket again and again (see dashboard section 5).
6. **Check quality on high-return products** (dashboard section 4) before reordering.

## Method
1. `sql/01_clean.sql` removes cancellations (moved to a returns table), non-product codes, zero or negative prices and quantities, exact duplicates, and large orders cancelled within 24 hours. Every rule is counted in `cleaning_log`.
2. `sql/02_trends.sql` monthly revenue, orders, customers, UK vs international, top products.
3. `sql/03_customers_rfm.sql` Recency, Frequency, Monetary scores (1 to 5) and six segments.
4. `sql/04_cohorts.sql` first-purchase-month cohorts and retention by month.
5. `sql/05_returns_and_baskets.sql` return rates by product and product pairs bought together.

## Data quality decisions worth knowing
- Two orders (80,995 and 74,215 units) were placed and cancelled within minutes. Left in, they add about GBP 245k of fake revenue and make two products look 100% returned. They are removed from both sales and returns.
- Dec 2011 is excluded from trends (data ends 9 Dec).
- Win-back and retention figures use stated assumptions. They show the size of the prize, not a prediction.

## Cleaning log
- raw rows: 1,067,371
- cancellation invoices (start with C) -> moved to returns: 19,494
- non-product codes (postage, fees, manual, samples, vouchers): 6,093
- zero or negative price (adjustments, write-offs): 6,207
- zero or negative quantity (not cancellations): 3,457
- rows with no customer id (kept for revenue, excluded from customer analysis): 243,007
- large orders cancelled within 24h (removed from sales and returns): 5
- exact duplicate lines removed: 33,663
- clean sales rows used for analysis: 1,003,209
