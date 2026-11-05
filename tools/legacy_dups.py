import hashlib, os, collections
root = r"C:\Users\rocel\THE-petrolumen"
legacy = os.path.join(root, "legacy_archive")
groups = collections.defaultdict(list)
for dp, dn, fn in os.walk(legacy):
    if "__pycache__" in dp: continue
    for f in fn:
        p = os.path.join(dp, f)
        try:
            if os.path.getsize(p) > 8_000_000: continue
            h = hashlib.sha256(open(p,'rb').read()).hexdigest()
        except Exception: continue
        groups[h].append(os.path.relpath(p, root))
dups = {h:v for h,v in groups.items() if len(v)>1}
tot = sum(os.path.getsize(os.path.join(root,v[0]))*(len(v)-1) for v in dups.values())
print("duplicate groups:", len(dups), "redundant copies:", sum(len(v)-1 for v in dups.values()), "redundant MB:", round(tot/1e6,1))
print("\nlargest groups:")
for h,v in sorted(dups.items(), key=lambda kv: -os.path.getsize(os.path.join(root,kv[1][0]))*(len(kv[1])-1))[:12]:
    print(f"  {len(v)}x {os.path.getsize(os.path.join(root,v[0])):>9} bytes :: {v[0]}")
    for x in v[1:3]: print("      dup:", x)
