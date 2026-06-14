"""
Focused verification sheet for the genuine in-boundary, figure-bearing core ONLY
(the cases that could populate the paper's empirical table). Small enough to verify
case-by-case against primary sources in one sitting.

Selects: category == service_economic_loss OR clear defamation/false-statement signal,
AND a monetary figure present. Pulls full report context + ALL source URLs, and adds
blank CONFIRM_* columns for the human pass (R8/R13).
"""
import ast, re
import pandas as pd

SNAP = "data/raw/mongodump_full_snapshot"
inc = pd.read_csv(f"{SNAP}/incidents.csv", low_memory=False)
rep = pd.read_csv(f"{SNAP}/reports.csv", low_memory=False)
rt = rep.set_index("report_number")[["text","url"]].to_dict("index")
ds = pd.read_csv("data/derived/ai_liability_severity_dataset.csv")

def rids(c):
    if pd.isna(c): return []
    try:
        v=ast.literal_eval(c); return [int(x) for x in v] if isinstance(v,(list,tuple)) else [int(v)]
    except Exception: return [int(x) for x in re.findall(r"\d+",str(c))]

def context_urls(iid):
    row = inc[inc.incident_id==iid].iloc[0]
    txt=[str(row.get("description",""))]; urls=[]
    for rid in rids(row.get("reports"))[:10]:
        r=rt.get(rid)
        if r:
            txt.append(str(r.get("text","")))
            u=str(r.get("url",""))
            if u and u!="nan" and u not in urls: urls.append(u)
    blob=re.sub(r"\s+"," "," ".join(txt))
    # keep a window around the first dollar/currency mention for the verifier
    m=re.search(r"(\$|£|€|US\$|CA\$|A\$|USD|CAD|AUD)\s?\d|won|\d\s?(million|billion)", blob, re.I)
    ctx = blob[max(0,m.start()-160):m.start()+200] if m else blob[:300]
    return ctx.strip(), urls

DEFAMATION = re.compile(r"defamat|defamed|false(ly)? (claim|statement|accus)|libel|reputation|falsely (stated|said)", re.I)
core = ds[(ds.category=="service_economic_loss") |
          (ds.title.str.contains(DEFAMATION, na=False))]
core = core[core.figure_1.astype(str).str.strip().ne("") & core.figure_1.notna()].copy()

rows=[]
for _,r in core.sort_values("incident_id").iterrows():
    ctx,urls = context_urls(int(r.incident_id))
    rows.append(dict(
        incident_id=int(r.incident_id), incident_url=r.incident_url,
        title=r.title, deployer=r.deployer, category=r.category,
        figure_extracted=r.figure_1, currency=r.currency_1, year=r.year,
        loss_type_guess=r.loss_type_guess, status_guess=r.status_guess,
        context=ctx, all_source_urls=" ; ".join(urls[:4]),
        CONFIRM_in_boundary="", CONFIRM_amount="", CONFIRM_currency="",
        CONFIRM_year="", CONFIRM_loss_type="", primary_source_url="", notes="",
    ))
out=pd.DataFrame(rows)
out.to_csv("data/derived/focused_verification.csv", index=False)
print(f"Focused core for human verification: {len(out)} cases -> data/derived/focused_verification.csv")
print("(verify each vs primary source; confirmed in-boundary PAID cases form the paper's Table)\n")
for _,r in out.iterrows():
    print(f"  #{r.incident_id:<5} {str(r.figure_extracted):<13} [{str(r.loss_type_guess)[:10]:<10}|{str(r.status_guess)[:9]:<9}] {str(r.title)[:56]}")
