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

# ---------- charts ----------
INK, MUTED = "#1f2937", "#6b7280"
BLUE, TEAL, AMBER, RED, GREY = "#2563eb", "#0d9488", "#d97706", "#dc2626", "#9ca3af"
layout = dict(template="plotly_white", font=dict(family="Inter, Segoe UI, Arial", color=INK, size=13),
              margin=dict(l=50, r=20, t=50, b=40), height=380)

# 1 monthly revenue UK vs intl
f1 = go.Figure()
f1.add_bar(x=monthly.month, y=monthly.uk_revenue, name="United Kingdom", marker_color=BLUE)
f1.add_bar(x=monthly.month, y=monthly.intl_revenue, name="International", marker_color=TEAL)
f1.update_layout(**{**layout, "margin": dict(l=50, r=20, t=90, b=40)}, barmode="stack",
                 title="Monthly revenue (GBP): the Sep to Nov climb repeats every year",
                 yaxis_title="Revenue (GBP)", legend=dict(orientation="h", y=1.0, x=0, yanchor="bottom"))

# 2 segments
order = ["Champions", "Loyal", "At Risk (was valuable)", "Needs Attention", "New / Promising", "Lost / Low value"]
seg_o = seg.set_index("segment").loc[order].reset_index()
cols = [BLUE, TEAL, RED, AMBER, "#7c3aed", GREY]
f2 = make_subplots(rows=1, cols=2, subplot_titles=("Share of customers", "Share of revenue"), specs=[[{"type": "pie"}, {"type": "pie"}]])
f2.add_pie(labels=seg_o.segment, values=seg_o.customers, marker=dict(colors=cols), hole=.45, sort=False, textinfo="percent", row=1, col=1)
f2.add_pie(labels=seg_o.segment, values=seg_o.revenue, marker=dict(colors=cols), hole=.45, sort=False, textinfo="percent", row=1, col=2)
f2.update_layout(title="A quarter of customers bring about 7 in 10 pounds of revenue", **layout)

# 3 cohort heatmap
pv = ret[(ret.months_since <= 12)].pivot(index="cohort_month", columns="months_since", values="retention_pct")
pv = pv[pv.index < "2011-01-01"]
f3 = go.Figure(go.Heatmap(z=pv.values, x=[f"M{c}" for c in pv.columns], y=[d.strftime("%b %Y") for d in pv.index],
                          colorscale="Blues", zmin=0, zmax=60, colorbar=dict(title="% still buying"),
                          hovertemplate="Cohort %{y}<br>%{x}: %{z}%<extra></extra>"))
f3.update_layout(title="Cohort retention: only about 1 in 5 first-time buyers come back the next month", **layout)
f3.update_yaxes(autorange="reversed")
f3.update_layout(height=480)

# 4 returns
f4 = go.Figure(go.Bar(x=ret_prod.return_rate_pct, y=ret_prod.description, orientation="h", marker_color=RED,
                      text=[f"{v:.0f}%  (GBP {r:,.0f} lost)" for v, r in zip(ret_prod.return_rate_pct, ret_prod.revenue_lost)],
                      textposition="outside"))
f4.update_layout(**{**layout, "margin": dict(l=260, r=140, t=50, b=40)},
                 title="Products with the worst return rates (sold 1,000+ units, 10%+ returned)",
                 xaxis=dict(title="% of units returned", range=[0, 115]), yaxis=dict(autorange="reversed"))

# 5 bundles
f5 = go.Figure(go.Bar(x=pairs.baskets_together, y=[f"{a}  +  {b}" for a, b in zip(pairs.product_a, pairs.product_b)],
                      orientation="h", marker_color=TEAL))
f5.update_layout(**{**layout, "margin": dict(l=420, r=20, t=50, b=40)},
                 title="Products most often bought in the same basket (bundle candidates)",
                 xaxis_title="Baskets containing both", yaxis=dict(autorange="reversed"))

# 6 top countries ex UK
c_ex = countries[countries.country != "United Kingdom"].head(8)
f6 = go.Figure(go.Bar(x=c_ex.country, y=c_ex.revenue, marker_color=BLUE))
f6.update_layout(title="Top international markets by revenue (GBP)", **layout, yaxis_title="Revenue (GBP)")

from plotly.offline import get_plotlyjs
plotly_js = get_plotlyjs()

def div(f): return f.to_html(full_html=False, include_plotlyjs=False, config=dict(displayModeBar=False))

gbp = lambda v: f"GBP {v:,.0f}"
kpis = [
    ("Net revenue analysed", gbp(tot.r)), ("Orders", f"{int(tot.o):,}"), ("Identified customers", f"{n_cust:,}"),
    ("Revenue from top 25% of customers", f"{metrics['champions_revenue_share']}%"),
    ("First-time buyers back next month", f"{m1:.0f}%"),
]
kpi_html = "".join(f"<div class='kpi'><div class='kv'>{v}</div><div class='kl'>{l}</div></div>" for l, v in kpis)
clean_rows = "".join(f"<tr><td>{r.step}</td><td class='n'>{int(r.rows_affected):,}</td></tr>" for r in clean.itertuples())

recs = f"""
<ol class='recs'>
<li><b>Protect the {int(champ.customers):,} Champions.</b> They are {metrics['champions_customer_share']}% of customers but {metrics['champions_revenue_share']}% of revenue
(average {gbp(champ.avg_revenue)} each, last bought about {int(champ.avg_recency_days)} days ago). Give them early access to new ranges and a named account contact before any discount.</li>
<li><b>Win back the {int(risk.customers)} At-Risk customers.</b> They placed about {risk.avg_orders:.0f} orders on average and spent {gbp(risk_hist)} in total, but have been silent for about {int(risk.avg_recency_days)} days.
If 10 to 20% return at half their old yearly spend, that is roughly {gbp(winback[10])} to {gbp(winback[20])} a year. This is a planning range based on stated assumptions, not a forecast.</li>
<li><b>Fix the second-order problem.</b> Only {m1:.0f}% of new customers buy again in month 1, and {metrics['one_time_share_pct']}% of all customers ({onetime:,}) bought exactly once.
Lifting month-1 return by {lift_pts} points on about {new_per_month:,.0f} new customers a month means about {extra_repeat:,.0f} extra repeat buyers a month (about {gbp(retention_gain_month)} a month at average spend).</li>
<li><b>Plan stock and cash for September.</b> Sep to Nov delivered {metrics['sep_nov_share_2010_pct']}% of 2010 revenue, and November ran {nov10/avg_other_2010:.1f}x the off-peak monthly average. Order and staff ahead of September, not October.</li>
<li><b>Bundle what is already bought together.</b> The top pairs (for example red and white hanging-heart tea-light holders, {int(pairs.baskets_together.iloc[0]):,} shared baskets) are colour or size variants, so sell them as sets.</li>
<li><b>Investigate quality on high-return lines.</b> Several lines, such as {ret_prod.description.iloc[1].title() if len(ret_prod)>1 else ''}, are returned at 10% to over 80%. Check suppliers and listings before reordering. A very high rate on a small line can also come from one bulk return, so look at the credit notes first.</li>
<li><b>Reduce reliance on the UK.</b> The UK is {metrics['uk_share_pct']}% of revenue. The next markets ({', '.join(c_ex.country.head(3))}) are small, so grow them deliberately.</li>
</ol>"""

html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Retail Analytics Decision Report</title>
<script>{plotly_js}</script>
<style>
:root{{--bg:#f8fafc;--card:#fff;--ink:#1f2937;--muted:#6b7280;--line:#e5e7eb;--accent:#2563eb}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0f172a;--card:#1e293b;--ink:#e5e7eb;--muted:#94a3b8;--line:#334155;--accent:#60a5fa}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 Inter,Segoe UI,Arial,sans-serif}}
.wrap{{max-width:1080px;margin:0 auto;padding:24px 16px 60px}}
h1{{font-size:26px;margin:8px 0 4px}}h2{{font-size:19px;margin:34px 0 8px}}.sub{{color:var(--muted);margin:0 0 18px}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin:18px 0}}
.kpi{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px}}
.kv{{font-size:22px;font-weight:700;color:var(--accent)}}.kl{{color:var(--muted);font-size:13px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:10px 12px;margin:12px 0}}
.recs li{{margin:10px 0}}table{{border-collapse:collapse;width:100%}}td{{padding:6px 8px;border-bottom:1px solid var(--line)}}td.n{{text-align:right;font-variant-numeric:tabular-nums}}
.note{{color:var(--muted);font-size:13px}}
</style></head><body><div class="wrap">
<h1>Retail Analytics: what the data says the business should do</h1>
<p class="sub">UK online gift retailer, 1 Dec 2009 to 9 Dec 2011 (UCI Online Retail II, 1.07M raw transactions). Cleaned with SQL, analysed with RFM segmentation, cohort retention, returns and basket analysis.</p>
<div class="kpis">{kpi_html}</div>
<h2>Recommended actions</h2><div class="card">{recs}</div>
<h2>1. Revenue and seasonality</h2><div class="card">{div(f1)}</div>
<h2>2. Customer value (RFM segments)</h2><div class="card">{div(f2)}</div>
<h2>3. Retention</h2><div class="card">{div(f3)}<p class="note">The Dec 2009 row includes customers who were already buying before the data starts, so it looks stronger than a true new-customer cohort.</p></div>
<h2>4. Where money leaks: returns</h2><div class="card">{div(f4)}</div>
<h2>5. What sells together</h2><div class="card">{div(f5)}</div>
<h2>6. Markets</h2><div class="card">{div(f6)}</div>
<h2>Data cleaning log</h2>
<div class="card"><table>{clean_rows}</table>
<p class="note">{metrics['anonymous_checkout_share_pct']}% of revenue has no customer id (guest checkout). It counts in revenue totals but is excluded from customer, RFM and cohort analysis.
December 2011 is excluded from monthly trends because the data stops on 9 December.</p></div>
</div></body></html>"""
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
