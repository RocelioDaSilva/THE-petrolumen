import ast, os, json
root = r"C:\Users\rocel\THE-petrolumen"
legacy_sets = {
 "gaia_new": r"legacy_archive\thepetrolumen\thepetrolumen_new\backend\gaia_genesis",
 "reservoir_eng": r"legacy_archive\reservoir_engineering",
}
cur_root = os.path.join(root, "backend", "app")

def scan(base):
    out={}
    for dp,dn,fn in os.walk(base):
        if "__pycache__" in dp: continue
        for f in fn:
            if not f.endswith(".py"): continue
            p=os.path.join(dp,f)
            try: t=ast.parse(open(p,encoding="utf-8",errors="replace").read())
            except Exception: continue
            ns=[n.name for n in t.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))]
            if ns: out[os.path.relpath(p,base)]=set(ns)
    return out

C=scan(cur_root); cur=set().union(*C.values())
for label,base in legacy_sets.items():
    L=scan(os.path.join(root,base))
    allsym=set().union(*L.values())
    print(f"\n### {label}: {len(L)} files, {len(allsym)} symbols; missing {len(allsym-cur)}")
    for rel,ns in sorted(L.items()):
        miss = ns-cur
        if ns and len(miss)==len(ns):
            print(f"  [ALL NEW] {rel}: {sorted(ns)[:8]}")
