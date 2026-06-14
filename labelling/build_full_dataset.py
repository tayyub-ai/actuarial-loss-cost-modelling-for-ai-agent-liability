"""
Most-complete public-data AI-liability severity screen achievable (honest ceiling).

Pipeline:
  1. Re-screen ALL 1,505 AIID incidents (not just the 163 money-matches) for the R17
     in-boundary class, improving recall (catches small/foreign-currency cases the money
     regex missed, e.g. Air Canada #639).
  2. Rich per-case extraction: parties, every monetary mention + type + currency + year,
     status keywords, all source URLs.
  3. Best-effort enrichment from CourtListener's free API (US court dockets/opinions).
  4. Emit an auditable dataset with explicit verification status.

This remains a litigation/disclosure-selected PUBLIC sample; a calibration-grade severity
dataset needs non-public insurer claims data. Nothing here is a "verified" figure until a
human confirms it against the cited primary source.
"""
import ast, re, json, time, urllib.parse, urllib.request
import pandas as pd

SNAP = "data/raw/mongodump_full_snapshot"
inc = pd.read_csv(f"{SNAP}/incidents.csv", low_memory=False)
rep = pd.read_csv(f"{SNAP}/reports.csv", low_memory=False)
rt = rep.set_index("report_number")[["title","text","url","date_published"]].to_dict("index")

def rids(c):
    if pd.isna(c): return []
    try:
        v=ast.literal_eval(c); return [int(x) for x in v] if isinstance(v,(list,tuple)) else [int(v)]
    except Exception: return [int(x) for x in re.findall(r"\d+",str(c))]

def gather(row):
    parts=[str(row.get("title","")),str(row.get("description",""))]; urls=[]; year=""
    for rid in rids(row.get("reports"))[:10]:
        r=rt.get(rid)
        if r:
            parts.append(str(r.get("text","")))
            u=str(r.get("url",""))
            if u and u!="nan" and u not in urls: urls.append(u)
            m=re.search(r"(20\d\d)",str(r.get("date_published","")))
            if m and not year: year=m.group(1)
    return re.sub(r"\s+"," "," ".join(parts)), urls, year

# ---- boundary logic (recall-improved) ----
EXCLUDE={
 "wrongful arrest/criminal":r"\bwrongful(ly)? arrest|false arrest|\bpolice\b|criminal charge|parole|recidivis|facial recogni.*arrest",
 "biometric/BIPA":r"\bbiometric|BIPA|faceprint|fingerprint scan",
 "physical/safety/AV":r"\bcrash|collision|autonomous vehicle|self-driving|pedestrian|bodily injur|car accident|physically (hurt|harm)",
 "employment/tenant":r"\bhiring algorithm|job applicant|tenant screen|SafeRent|resume screen|employment discriminat",
 "govt benefit/welfare":r"\bwelfare|unemployment benefit|medicaid|MiDAS|public assistance|benefits algorithm",
 "data-breach/privacy class":r"\bdata breach|illegally collect|wiretap|eavesdrop",
 "first-party deepfake scam":r"\bdeepfake (scam|fraud|voice|video) |voice clon.*scam|impersonat.*(wired|transfer)",
}
SERVICE=r"\bchatbot|\bbot\b|\bLLM\b|generative ai|\bGPT\b|virtual assistant|ai (advisor|advice|assistant|tool|system|model|agent|chatbot)|ai-generated|hallucinat|copilot|recommendation engine"
LOSSCTX=r"\b(settle|settled|settlement|awarded|damages|ordered to pay|compensat|refund|sued|lawsuit|liable|liability|tribunal|judg(e)?ment|verdict|fine|fined|penalt|class action|restitution)\b"

AMT=re.compile(r"(\$|US\$|USD|CA\$|C\$|A\$|£|€|CAD|AUD)\s?(\d[\d,]*(?:\.\d+)?)\s?(million|billion|m|bn|k)?"
               r"|(\d[\d,]*(?:\.\d+)?)\s?(million|billion)?\s?(won|yuan|euros|pounds|rupees|dollars)",re.I)
def currency(s):
    s=s.lower()
    for k,v in [("c$","CAD"),("ca$","CAD"),("cad","CAD"),("a$","AUD"),("aud","AUD"),("£","GBP"),("pounds","GBP"),
                ("€","EUR"),("euros","EUR"),("won","KRW"),("yuan","CNY"),("rupees","INR"),("us$","USD"),("usd","USD"),("$","USD")]:
        if k in s: return v
    return ""
LT={"settlement":r"settle|settled|agreed to pay","award_judgment":r"awarded|damages of|ordered to pay|judg|verdict|tribunal ordered|tribunal found",
    "fine_penalty":r"\bfine|fined|penalt|sanction","demand":r"seeks|sued for|lawsuit seeks|demand|prayer for relief"}
STATUS={"resolved_paid":r"settle|settled|awarded|ordered to pay|paid|judgment for|fined",
        "pending":r"pending|filed|ongoing|lawsuit (was|is) filed|sues|suing","dismissed":r"dismiss|thrown out|rejected"}

def figures(text):
    out=[]
    for m in AMT.finditer(text):
        s=m.group(0); a,b=max(0,m.start()-60),min(len(text),m.end()+60)
        out.append((s.strip(), currency(s), re.sub(r"\s+"," ",text[a:b]).strip()))
        if len(out)>=4: break
    return out
def tag(text,pats):
    return next((k for k,p in pats.items() if re.search(p,text,re.I)),"")

# coarse category to separate the genuine service-economic-loss class from noise
CATEGORY={
 "copyright_IP":r"copyright|pirat|training data|infring|intellectual property|scrap.*(book|article|lyric|content)|unauthorized.*(book|work)s",
 "lawyer_sanction":r"sanction|fake (legal )?citation|fabricated (case|citation)|hallucinated (case|citation)|disqualif|nonexistent case|bogus citation",
 "regulatory_fine":r"\bSEC\b|\bFTC\b|regulator|securities|ASIC|data protection authority|\bACCC\b",
 "service_economic_loss":r"chatbot.*(wrong|inaccurate|incorrect|refund|advice|promis)|hallucinat.*(advice|customer|client|user)|"
   r"(ai|chatbot|bot|assistant).*(wrong(ly)?|inaccurat|incorrect).*(advice|inform|told|quote|price|refund)|"
   r"unauthorized (purchase|transaction|order)|deleted (the )?(production )?database|wrong(ly)? (advised|told|quoted|informed)|"
   r"bereavement|misquoted (a )?(price|fare)|gave (incorrect|wrong)",
}
def category(text):
    return tag(text,CATEGORY) or "other"

rows=[]
for _,row in inc.iterrows():
    text,urls,year=gather(row)
    excl=[l for l,p in EXCLUDE.items() if re.search(p,text,re.I)]
    has_service=bool(re.search(SERVICE,text,re.I)); has_loss=bool(re.search(LOSSCTX,text,re.I))
    in_b=(not excl) and has_service and has_loss
    if not in_b: continue
    figs=figures(text)
    rows.append(dict(
        incident_id=int(row["incident_id"]),
        incident_url=f"https://incidentdatabase.ai/cite/{int(row['incident_id'])}/",
        title=re.sub(r"\s+"," ",str(row.get("title","")))[:110],
        deployer=str(row.get("Alleged deployer of AI system",""))[:60],
        year=year,
        figure_1=figs[0][0] if figs else "", currency_1=figs[0][1] if figs else "",
        figure_context=figs[0][2] if figs else "",
        other_figures=" | ".join(f"{f[0]}({f[1]})" for f in figs[1:]) if len(figs)>1 else "",
        category=category(text),
        loss_type_guess=tag(text,LT), status_guess=tag(text,STATUS),
        source_url=urls[0] if urls else "",
        courtlistener_match="", verify_status="NEEDS PRIMARY-SOURCE CONFIRMATION",
    ))

d=pd.DataFrame(rows).sort_values("incident_id")
print(f"Full re-screen of 1,505 AIID incidents -> {len(d)} in-boundary candidates (recall-improved).")
print(f"  Air Canada #639 captured: {'YES' if 639 in set(d.incident_id) else 'NO'}")
print(f"  with an extractable figure: {len(d[d.figure_1!=''])}")

# ---- CourtListener enrichment (free API; best-effort, capped) ----
def cl_lookup(q):
    try:
        url="https://www.courtlistener.com/api/rest/v4/search/?"+urllib.parse.urlencode({"q":q,"type":"o"})
        req=urllib.request.Request(url,headers={"User-Agent":"research-screen/1.0"})
        with urllib.request.urlopen(req,timeout=20) as r:
            j=json.load(r)
        if j.get("count"):
            top=j["results"][0]
            return f"{j['count']} hits; top: {top.get('caseName','?')} ({top.get('court','?')})"
    except Exception as e:
        return f"(lookup failed: {type(e).__name__})"
    return "no US court match"

DO_CL = False  # prior run: 9/144 US-court hits (most AI matters are recent district dockets
               # or foreign/Canadian tribunals absent from the opinion corpus). Skipped for speed.
if DO_CL:
    matched=0
    for i in d.index:
        dep=d.at[i,"deployer"].split(",")[0].strip()
        if not dep or dep.lower() in ("nan",""): continue
        res=cl_lookup(f'"{dep}" artificial intelligence'); d.at[i,"courtlistener_match"]=res
        if res and "hits" in res: matched+=1
    print(f"  CourtListener: {matched} US-court hits of {len(d[d.deployer!=''])} named deployers.")
else:
    print("\nCourtListener enrichment: skipped (prior run 9/144; US opinion corpus misses recent/foreign AI dockets).")

print("\nCategory breakdown (separating genuine service-loss from copyright/sanction/fine noise):")
print(d.category.value_counts().to_string())
svc = d[d.category=="service_economic_loss"]
print(f"\n>>> Genuine 'AI service -> third-party economic loss' candidates: {len(svc)} (the in-boundary core)")
print(f"    of which resolved_paid with a figure: {len(svc[(svc.status_guess=='resolved_paid')&(svc.figure_1.astype(str)!='')])}")

d.to_csv("data/derived/ai_liability_severity_dataset.csv",index=False)
print(f"\nWrote data/derived/ai_liability_severity_dataset.csv ({len(d)} rows).")
print("\nIn-boundary candidates with figures (verify each vs primary source):")
for _,r in d[d.figure_1!=''].iterrows():
    print(f"  #{r.incident_id:<5} {r.figure_1:<13}{('['+r.currency_1+']') if r.currency_1 else '':<7}[{r.loss_type_guess or '?':<12}|{r.status_guess or '?':<13}] {r.title[:50]}")
