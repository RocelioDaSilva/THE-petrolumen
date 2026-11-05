import ast, os, json, re
root = r"C:\Users\rocel\THE-petrolumen"
legacy = os.path.join(root, "legacy_archive", "thepetrolumen", "thepetrolumen_new", "backend", "gaia_genesis")
current = os.path.join(root, "backend", "app")

def scan(base):
    out = {}
    for dp, dn, fn in os.walk(base):
        if "__pycache__" in dp: continue
        for f in fn:
            if not f.endswith(".py"): continue
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, base)
            try: tree = ast.parse(open(p, encoding="utf-8", errors="replace").read())
            except Exception as e: continue
            names = set()
            for n in tree.body:
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    names.add(n.name)
            out[rel] = names
    return out

L, C = scan(legacy), scan(current)
legacy_names = set().union(*L.values()) if L else set()
current_names = set().union(*C.values()) if C else set()
print("legacy files", len(L), "current files", len(C))
print("legacy symbols", len(legacy_names), "current symbols", len(current_names))
missing = sorted(legacy_names - current_names)
print("symbols only in legacy:", len(missing))
for m in missing: print("  ", m)
