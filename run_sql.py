"""Run the SQL pipeline in order and build warehouse.duckdb."""
import duckdb, glob, os, sys

DB = "warehouse.duckdb"
if os.path.exists(DB):
    os.remove(DB)
con = duckdb.connect(DB)
for f in sorted(glob.glob("sql/*.sql")):
    print("running", f)
    con.execute(open(f, encoding="utf-8").read())
con.close()
print("done ->", DB)
