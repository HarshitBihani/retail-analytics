"""Download the UCI Online Retail II dataset and convert it to parquet (about 2 minutes, mostly reading the Excel file).
Run once:  python prepare_data.py
"""
import io, os, urllib.request, zipfile
import pandas as pd

URL = "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip"
os.makedirs("raw", exist_ok=True)
xlsx = "raw/online_retail_II.xlsx"
if not os.path.exists(xlsx):
    print("downloading (46 MB)...")
    with urllib.request.urlopen(URL) as r:
        zipfile.ZipFile(io.BytesIO(r.read())).extract("online_retail_II.xlsx", "raw")

print("reading both sheets (slow, Excel)...")
sheets = pd.read_excel(xlsx, sheet_name=None, engine="openpyxl")
df = pd.concat(sheets.values(), ignore_index=True)
df.columns = ["invoice", "stock_code", "description", "quantity", "invoice_date", "price", "customer_id", "country"]
for c in ["invoice", "stock_code", "description", "country"]:   # mixed int/str in the source
    df[c] = df[c].astype("string")
df.to_parquet("raw/online_retail_ii.parquet")
print("rows:", len(df), "-> raw/online_retail_ii.parquet")
