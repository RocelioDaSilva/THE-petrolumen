import os, difflib, collections
root = r"C:\Users\rocel\THE-petrolumen"
legacy_roots = [
 r"legacy_archive\reservoir_engineering",
 r"legacy_archive\thepetrolumen\thepetrolumen_new\backend\gaia_genesis",
]
cur_root = os.path.join(root, "backend", "app")

def pyfiles(base):
    out=[]
    for dp,dn,fn in os.walk(base):
        if "__pycache__" in dp: continue
        for f in fn:
            if f.endswith(".py"): out.append(os.path.join(dp,f))
    return out

cur = pyfiles(cur_root)
curtext = {p: open(p,encoding="utf-8",errors="replace").read() for p in cur}
legacy = pyfiles(os.path.join(root, legacy_roots[0])) + pyfiles(os.path.join(root, legacy_roots[1]))
seen=set(); rows=[]
for lp in legacy:
    if lp in seen: continue
    seen.add(lp)
    lt = open(lp,encoding="utf-8",errors="replace").read()
    if len(lt) < 200: continue
    best=(0,None)
    for cp,ct in curtext.items():
        if abs(len(ct)-len(lt)) > max(len(lt),len(ct))*0.7: continue
        r = difflib.SequenceMatcher(None, lt, ct).quick_ratio()
        if r > best[0]:
            best=(r,cp)
    rows.append((best[0], os.path.relpath(lp,root), os.path.relpath(best[1],root) if best[1] else "-", len(lt)))
rows.sort(reverse=True)
print("legacy files compared:", len(rows))
print("\n>=0.90 similarity (already absorbed):")
for r,lp,cp,n in rows:
    if r>=0.90: print(f"  {r:.2f} {lp}  ->  {cp}")
print("\n0.60-0.89 (partially absorbed / divergent):")
for r,lp,cp,n in rows:
    if 0.60<=r<0.90: print(f"  {r:.2f} {lp}  ->  {cp}")
print("\n<0.60 (no current counterpart):")
for r,lp,cp,n in rows:
    if r<0.60: print(f"  {r:.2f} {lp}  ({n} bytes)")
