"""Genera docs/_build/html/index.html (dashboard autocontenido) a partir de data/superstore_transformado.csv."""
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
df = pd.read_csv(ROOT / "data" / "superstore_transformado.csv")

lk = {
    "region": sorted(df["Region"].unique()),
    "cat": sorted(df["Category"].unique()),
    "sub": sorted(df["Sub-Category"].unique()),
    "seg": sorted(df["Segment"].unique()),
    "state": sorted(df["State"].unique()),
}
idx = {k: {v: i for i, v in enumerate(vals)} for k, vals in lk.items()}
orders = {o: i for i, o in enumerate(df["Order ID"].unique())}

rows = [
    [r.Order_Date[:7], idx["region"][r.Region], idx["cat"][r.Category], idx["sub"][r.SubCategory],
     idx["seg"][r.Segment], idx["state"][r.State], orders[r.OrderID],
     round(r.Sales, 2), round(r.Profit, 2), int(r.Quantity), float(r.Discount)]
    for r in df.rename(columns={"Sub-Category": "SubCategory", "Order ID": "OrderID"}).itertuples()
]
payload = json.dumps({"lookups": lk, "rows": rows}, separators=(",", ":"), ensure_ascii=False)

html = (ROOT / "src" / "template.html").read_text(encoding="utf-8")
html = html.replace("/*__CHARTJS__*/", (ROOT / "src" / "chart.umd.js").read_text(encoding="utf-8"))
html = html.replace("/*__DATA__*/", payload)

out = ROOT / "docs" / "_build" / "html"
out.mkdir(parents=True, exist_ok=True)
(out / "index.html").write_text(html, encoding="utf-8")
(out / ".nojekyll").write_text("")
print(f"OK -> {out/'index.html'} ({len(html)/1024:.0f} KB, {len(rows)} filas)")
