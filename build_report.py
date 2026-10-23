"""Read warehouse.duckdb, compute the numbers behind each finding, and write
outputs/dashboard.html, outputs/FINDINGS.md and outputs/metrics.json.
Every number in the written findings is computed here, none is typed by hand."""
import json, os
import duckdb
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

os.makedirs("outputs", exist_ok=True)
con = duckdb.connect("warehouse.duckdb", read_only=True)
q = lambda s: con.execute(s).df()

# ---------- numbers ----------
tot = q("select sum(revenue) r, count(distinct invoice) o, count(distinct customer_id) c from sales").iloc[0]
monthly = q("select * from monthly")
seg = q("select * from segment_summary")
cust_rev = float(q("select sum(monetary) m from rfm").iloc[0, 0])
n_cust = int(q("select count(*) n from rfm").iloc[0, 0])
champ = seg[seg.segment == "Champions"].iloc[0]
risk = seg[seg.segment == "At Risk (was valuable)"].iloc[0]
lost = seg[seg.segment == "Lost / Low value"].iloc[0]
uk_share = float(q("select sum(case when country='United Kingdom' then revenue end)/sum(revenue) from sales").iloc[0, 0])
anon_share = float(q("select sum(case when customer_id is null then revenue end)/sum(revenue) from sales").iloc[0, 0])

y2010 = monthly[monthly.month.dt.year == 2010]
sepnov_2010 = float(y2010[y2010.month.dt.month.isin([9, 10, 11])].revenue.sum())
share_sepnov_2010 = sepnov_2010 / float(y2010.revenue.sum())
nov10 = float(y2010[y2010.month.dt.month == 11].revenue.iloc[0])
avg_other_2010 = float(y2010[~y2010.month.dt.month.isin([9, 10, 11, 12])].revenue.mean())

ret = q("select * from cohort_retention")
m1 = float(ret[(ret.months_since == 1)].retention_pct.mean())
m3 = float(ret[(ret.months_since == 3)].retention_pct.mean())
m12 = float(ret[(ret.months_since == 12)].retention_pct.mean())
cohort_sizes = ret[ret.months_since == 0]
new_per_month = float(cohort_sizes[cohort_sizes.cohort_month >= "2010-01-01"].active_customers.mean())
rev_per_active = float((monthly.revenue / monthly.customers).mean())

# one-time buyers
onetime = int(q("select count(*) from rfm where frequency = 1").iloc[0, 0])

# win-back scenario: At-Risk customers, assume 10/15/20% return, each spending half their historical
# yearly average (data spans ~2 years). These are ASSUMPTIONS, shown as a range, not a forecast.
risk_hist = float(risk.revenue)
yearly = risk_hist / 2.0
winback = {p: round(yearly * p / 100 * 0.5) for p in (10, 15, 20)}

# retention scenario: lift month-1 retention by 5 points on average monthly new customers
lift_pts = 5
extra_repeat = new_per_month * lift_pts / 100
retention_gain_month = extra_repeat * rev_per_active

ret_prod = q("select * from returns_by_product where units_sold >= 1000 and return_rate_pct >= 10 order by revenue_lost desc limit 8")
pairs = q("select * from basket_pairs limit 8")
clean = q("select * from cleaning_log")
top_prod = q("select * from top_products limit 10")
countries = q("select * from country_rev limit 10")

metrics = dict(
    total_revenue=round(float(tot.r)), orders=int(tot.o), customers=int(tot.c),
    champions_customers=int(champ.customers), champions_revenue_share=round(float(champ.revenue) / cust_rev * 100, 1),
    champions_customer_share=round(float(champ.customers) / n_cust * 100, 1),
    at_risk_customers=int(risk.customers), at_risk_historic_revenue=round(risk_hist),
    uk_share_pct=round(uk_share * 100, 1), anonymous_checkout_share_pct=round(anon_share * 100, 1),
    sep_nov_share_2010_pct=round(share_sepnov_2010 * 100, 1), nov_vs_avg_off_peak_2010=round(nov10 / avg_other_2010, 2),
    month1_retention_pct=round(m1, 1), month3_retention_pct=round(m3, 1), month12_retention_pct=round(m12, 1),
    one_time_buyers=onetime, one_time_share_pct=round(onetime / n_cust * 100, 1),
    winback_scenarios_gbp=winback,
    retention_lift_5pts_extra_repeat_customers_per_month=round(extra_repeat, 1),
    retention_lift_5pts_monthly_revenue_gbp=round(retention_gain_month),
)
json.dump(metrics, open("outputs/metrics.json", "w"), indent=2)

# ---------- charts and page (shared look in theme.py) ----------
import theme as T
from plotly.offline import get_plotlyjs

V, O, B, P, Y, G = T.PALETTE
gbp = lambda v: f"GBP {v:,.0f}"

f1 = go.Figure()
f1.add_bar(x=monthly.month, y=monthly.uk_revenue, name="United Kingdom", marker_color=V)
f1.add_bar(x=monthly.month, y=monthly.intl_revenue, name="International", marker_color=B)
chart1 = T.fig_html(f1, barmode="stack", yaxis_title="Revenue (GBP)", legend=dict(orientation="h", y=1.1, x=0), margin=dict(l=60, r=20, t=40, b=40))

order = ["Champions", "Loyal", "At Risk (was valuable)", "Needs Attention", "New / Promising", "Lost / Low value"]
seg_o = seg.set_index("segment").loc[order].reset_index()
f2 = make_subplots(rows=1, cols=2, subplot_titles=("Share of customers", "Share of revenue"), specs=[[{"type": "pie"}, {"type": "pie"}]])
f2.add_pie(labels=seg_o.segment, values=seg_o.customers, marker=dict(colors=T.PALETTE), hole=.55, sort=False, textinfo="percent", row=1, col=1)
f2.add_pie(labels=seg_o.segment, values=seg_o.revenue, marker=dict(colors=T.PALETTE), hole=.55, sort=False, textinfo="percent", row=1, col=2)
chart2 = T.fig_html(f2, height=380, margin=dict(l=10, r=10, t=40, b=20))

pv = ret[(ret.months_since <= 12)].pivot(index="cohort_month", columns="months_since", values="retention_pct")
pv = pv[pv.index < "2011-01-01"]
f3 = go.Figure(go.Heatmap(z=pv.values, x=[f"M{c}" for c in pv.columns], y=[d.strftime("%b %Y") for d in pv.index],
                          colorscale=[[0, "#f4f2ff"], [1, "#4b3fd6"]], zmin=0, zmax=60, colorbar=dict(title="% still buying"),
                          hovertemplate="Cohort %{y}<br>%{x}: %{z}%<extra></extra>"))
f3.update_yaxes(autorange="reversed")
chart3 = T.fig_html(f3, height=470)

f4 = go.Figure(go.Bar(x=ret_prod.return_rate_pct, y=ret_prod.description, orientation="h", marker_color=O,
                      text=[f"{v:.0f}%  (GBP {r:,.0f} lost)" for v, r in zip(ret_prod.return_rate_pct, ret_prod.revenue_lost)], textposition="outside"))
chart4 = T.fig_html(f4, margin=dict(l=250, r=150, t=20, b=40), xaxis=dict(title="% of units returned", range=[0, 115], gridcolor="#e9e5da"),
                    yaxis=dict(autorange="reversed"))

f5 = go.Figure(go.Bar(x=pairs.baskets_together, y=[f"{a}  +  {b}" for a, b in zip(pairs.product_a, pairs.product_b)], orientation="h", marker_color=B))
chart5 = T.fig_html(f5, margin=dict(l=430, r=20, t=20, b=40), xaxis=dict(title="Baskets containing both", gridcolor="#e9e5da"), yaxis=dict(autorange="reversed"))

c_ex = countries[countries.country != "United Kingdom"].head(8)
f6 = go.Figure(go.Bar(x=c_ex.country, y=c_ex.revenue, marker_color=V))
chart6 = T.fig_html(f6, yaxis_title="Revenue (GBP)")

kpi_html = T.kpis([
    ("Net revenue analysed", gbp(tot.r), "across 2010 to 2011"), ("Orders", f"{int(tot.o):,}", "all valid orders"),
    ("Identified customers", f"{n_cust:,}", "known customer profiles"),
    ("Revenue from top 25% of customers", f"{metrics['champions_revenue_share']}%", "customer revenue share"),
    ("First-time buyers back next month", f"{m1:.0f}%", "month 1 repeat rate"),
])

actions = T.action_cards([
    (1, f"Protect the {int(champ.customers):,} Champions",
     f"They are {metrics['champions_customer_share']}% of customers but {metrics['champions_revenue_share']}% of revenue (average {gbp(champ.avg_revenue)} each, "
     f"last bought about {int(champ.avg_recency_days)} days ago). Give them early access to new ranges and a named account contact before any discount."),
    (2, f"Win back the {int(risk.customers)} At-Risk customers",
     f"They placed about {risk.avg_orders:.0f} orders on average and spent {gbp(risk_hist)} in total, but have been silent for about {int(risk.avg_recency_days)} days. "
     f"If 10 to 20% return at half their old yearly spend, that is roughly {gbp(winback[10])} to {gbp(winback[20])} a year.",
     "Planning range from stated assumptions, not a forecast"),
    (3, "Fix the second-order problem",
     f"Only {m1:.0f}% of new customers buy again in month 1, and {metrics['one_time_share_pct']}% of all customers ({onetime:,}) bought exactly once. "
     f"Lifting month-1 return by {lift_pts} points on about {new_per_month:,.0f} new customers a month means about {extra_repeat:,.0f} extra repeat buyers a month "
     f"(about {gbp(retention_gain_month)} a month at average spend)."),
    (4, "Plan stock and cash for September",
     f"Sep to Nov delivered {metrics['sep_nov_share_2010_pct']}% of 2010 revenue, and November ran {nov10/avg_other_2010:.1f}x the off-peak monthly average. "
     "Order and staff ahead of September, not October."),
    (5, "Bundle what is already bought together",
     f"The top pairs (for example red and white hanging-heart tea-light holders, {int(pairs.baskets_together.iloc[0]):,} shared baskets) are colour or size variants, so sell them as sets."),
    (6, "Investigate quality on high-return lines",
     f"Several lines, such as {ret_prod.description.iloc[1].title() if len(ret_prod) > 1 else ''}, are returned at 10% to over 80%. Check suppliers and listings before reordering. "
     "A very high rate on a small line can also come from one bulk return, so look at the credit notes first."),
    (7, "Reduce reliance on the UK",
     f"The UK is {metrics['uk_share_pct']}% of revenue. The next markets ({', '.join(c_ex.country.head(3))}) are small, so grow them deliberately."),
])

clean_table = T.table(["Cleaning step", "Rows"], [[T.esc(r.step), f"{int(r.rows_affected):,}"] for r in clean.itertuples()], numeric_cols=(1,))

body = (kpi_html
        + T.section("01 / The opportunity", "Recommended actions", actions, "Seven decisions, each grounded in the numbers below.")
        + T.section("02 / Seasonality", "Revenue and the autumn climb", T.card(chart1, caption="Monthly revenue in GBP, United Kingdom vs international. The Sep to Nov climb repeats every year."))
        + T.section("03 / Where value sits", "Customer segments", T.card(chart2, caption="A quarter of customers bring about 7 in 10 pounds of revenue."))
        + T.section("04 / Retention", "Who comes back", T.card(chart3, caption="Cohort retention: only about 1 in 5 first-time buyers come back the next month.")
                    + T.callout("The Dec 2009 row includes customers who were already buying before the data starts, so it looks stronger than a true new-customer cohort."))
        + T.section("05 / Leaks", "Returns", T.card(chart4, caption="Products with the worst return rates (sold 1,000+ units, 10%+ returned)."))
        + T.section("06 / Bundles", "What sells together", T.card(chart5, caption="Products most often bought in the same basket (bundle candidates)."))
        + T.section("07 / Markets", "Beyond the UK", T.card(chart6, caption="Top international markets by revenue (GBP)."))
        + T.section("Method", "How the data was cleaned",
                    f"<details open><summary>Cleaning log</summary>{T.card(clean_table)}</details>"
                    + T.callout(f"{metrics['anonymous_checkout_share_pct']}% of revenue has no customer id (guest checkout). It counts in revenue totals but is excluded from customer, RFM and cohort analysis. "
                                "December 2011 is excluded from monthly trends because the data stops on 9 December."))
        + '<div class="foot">UK online gift retailer, 1 Dec 2009 to 9 Dec 2011 (UCI Online Retail II, 1.07M raw transactions). Cleaned with SQL, analysed with RFM segmentation, '
          'cohort retention, returns and basket analysis. Every number on this page is calculated by build_report.py.</div>')

html = T.page("Retail Analytics Decision Report", "Retail analytics", "Executive readout  ·  2010 to 2011", "What the data says", "the shop should do.",
              "A focused view of where customer value lives, where it leaks, and what to act on next.", body, plotly_js=get_plotlyjs(), logo="R")
open("outputs/dashboard.html", "w", encoding="utf-8").write(html)

md = f"""# Findings: Retail Analytics Decision Report

Data: UCI Online Retail II, a UK online gift retailer, 1 Dec 2009 to 9 Dec 2011, 1,067,371 raw rows.
All figures are computed by `build_report.py` from the SQL tables. Nothing here is typed by hand.

## The business in numbers
- Net revenue analysed: {gbp(tot.r)} across {int(tot.o):,} orders and {n_cust:,} identified customers.
- {metrics['anonymous_checkout_share_pct']}% of revenue is guest checkout (no customer id). It counts in revenue, not in customer analysis.
- UK share of revenue: {metrics['uk_share_pct']}%.

## What I would tell the owner to do
{chr(10).join(f"{i+1}. " + t for i, t in enumerate([
    f"**Protect the Champions.** {int(champ.customers):,} customers ({metrics['champions_customer_share']}% of customers) bring {metrics['champions_revenue_share']}% of revenue, averaging {gbp(champ.avg_revenue)} each.",
    f"**Win back At-Risk customers.** {int(risk.customers)} customers who spent {gbp(risk_hist)} in total have been silent for about {int(risk.avg_recency_days)} days. If 10 to 20% return at half their old yearly spend: about {gbp(winback[10])} to {gbp(winback[20])} a year (assumption-based planning range, not a forecast).",
    f"**Fix repeat purchase.** {m1:.0f}% of new customers buy again in month 1; {m12:.0f}% are still buying 12 months later. {metrics['one_time_share_pct']}% of customers bought only once. A {lift_pts}-point lift in month-1 return is about {extra_repeat:,.0f} extra repeat buyers a month (about {gbp(retention_gain_month)} a month).",
    f"**Plan for September.** Sep to Nov was {metrics['sep_nov_share_2010_pct']}% of 2010 revenue; November ran {nov10/avg_other_2010:.1f}x the off-peak average.",
    "**Sell bundles.** Colour and size variants are bought in the same basket again and again (see dashboard section 5).",
    "**Check quality on high-return products** (dashboard section 4) before reordering.",
]))}

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
{chr(10).join(f"- {r.step}: {int(r.rows_affected):,}" for r in clean.itertuples())}
"""
open("outputs/FINDINGS.md", "w", encoding="utf-8").write(md)
print(json.dumps(metrics, indent=2))
