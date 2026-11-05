@'
import os, re, json

ROOT = "."
SKIP_DIRS = {"node_modules", ".git", "legacy_archive", ".venv", "__pycache__", "dist", "build"}
BOM = b"\xef\xbb\xbf"

def walk_files():
    for r, ds, fs in os.walk(ROOT):
        ds[:] = [d for d in ds if d not in SKIP_DIRS]
        for f in fs:
            yield os.path.join(r, f)

def read(p):
    try:
        return open(p, "rb").read()
    except OSError:
        return b""

print("=" * 70)
print("AUDIT SCAN — " + os.getcwd())
print("=" * 70)

# B2: BOM files
bom_hits = [p for p in walk_files() if read(p)[:3] == BOM]
print(f"\n[B2] BOM files: {len(bom_hits)}")
for p in bom_hits[:20]:
    print("     " + p)

# B1: conflict markers anywhere in backend/app
conflict_hits = []
for p in walk_files():
    if not p.endswith((".py", ".ts", ".tsx", ".json", ".yml", ".yaml")):
        continue
    src = read(p).decode("utf-8", "ignore")
    if re.search(r"^(<<<<<<<|=======|>>>>>>>)", src, re.M):
        conflict_hits.append(p)
print(f"\n[B1] Files with conflict markers: {len(conflict_hits)}")
for p in conflict_hits[:20]:
    print("     " + p)

# B1b: main.py structure
mp = os.path.join("backend", "app", "main.py")
if os.path.exists(mp):
    src = read(mp).decode("utf-8", "ignore")
    print(f"\n[B1b] main.py: {len(src)} chars, "
          f"RedirectResponse={src.count('RedirectResponse')}, "
          f"include_router={src.count('include_router')}")
else:
    print(f"\n[B1b] main.py NOT FOUND at {mp}")

# B3: pywin32 in requirements
req = os.path.join("backend", "requirements.txt")
if os.path.exists(req):
    src = read(req).decode("utf-8", "ignore").lower()
    has_win32 = "pywin32" in src
    print(f"\n[B3] backend/requirements.txt exists, pywin32 present: {has_win32}")
    if has_win32:
        for line in src.splitlines():
            if "pywin32" in line:
                print("     " + line.strip())
else:
    print(f"\n[B3] backend/requirements.txt MISSING")

# B4: ppes declared anywhere
ppes_decl = []
for name in ("backend/requirements.txt", "backend/requirements-dev.txt",
             "backend/pyproject.toml", "pyproject.toml", "requirements.txt"):
    if os.path.exists(name):
        src = read(name).decode("utf-8", "ignore").lower()
        if "ppes" in src:
            for line in src.splitlines():
                if "ppes" in line.lower():
                    ppes_decl.append(f"{name}: {line.strip()}")
print(f"\n[B4] ppes dependency declarations: {len(ppes_decl)}")
for d in ppes_decl:
    print("     " + d)
print(f"     ppes-reference dir exists: {os.path.isdir('ppes-reference')}")

# B5: the 7 missing bridge names
bridge = os.path.join("backend", "app", "engines", "reservoir", "ppes_bridge.py")
missing = ["ballooning_effect", "piston_effect", "port_diameter_from_area",
           "size_orifice_port", "wichert_aziz_correction",
           "mu_gas_low_pressure", "oil_compressibility"]
if os.path.exists(bridge):
    src = read(bridge).decode("utf-8", "ignore")
    print(f"\n[B5] ppes_bridge.py: {len(src)} chars")
    for name in missing:
        imported = bool(re.search(rf"import[^\n]*\b{name}\b", src))
        defined = bool(re.search(rf"^def {name}\b", src, re.M))
        status = "OK" if (not imported or defined) else "MISSING-DEF"
        print(f"     {name:30s} imported={imported} defined={defined} {status}")
else:
    print(f"\n[B5] ppes_bridge.py NOT FOUND at {bridge}")

# B6: CI workflow
wf = []
for name in (".github/workflows/ci.yml", ".github/workflows/backend-ci.yml"):
    if os.path.exists(name):
        src = read(name).decode("utf-8", "ignore")
        wf.append((name, len(src)))
print(f"\n[B6] CI workflows: {len(wf)}")
for name, n in wf:
    print(f"     {name} ({n} chars)")

# ppes-reference tests
tests = os.path.join("ppes-reference", "tests", "test_book_examples.py")
if os.path.exists(tests):
    print(f"\n[REF] ppes-reference/tests/test_book_examples.py exists")
else:
    print(f"\n[REF] ppes book-example tests NOT FOUND")

print("\n" + "=" * 70)
print("END")
print("=" * 70)
'@ | Out-File -Encoding utf8 -FilePath audit_scan.py

python audit_scan.py