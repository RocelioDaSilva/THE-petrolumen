import ast, os
root=r"C:\Users\rocel\THE-petrolumen"
pairs=[
 ("legacy_archive/reservoir_engineering/flow_simulation/reservoir_simulator.py","backend/app/engines/reservoir/simulation/flow_simulation.py"),
 ("legacy_archive/reservoir_engineering/flow_simulation/flow_simulator.py","backend/app/engines/reservoir/simulation/flow_simulation.py"),
 ("legacy_archive/reservoir_engineering/flow_simulation/eclipse_simulator.py","backend/app/engines/reservoir/simulation/commercial_simulator.py"),
 ("legacy_archive/reservoir_engineering/well_testing/well_test.py","backend/app/engines/reservoir/reservoir_engineering.py"),
 ("legacy_archive/reservoir_engineering/static_modeling/static_model.py","backend/app/engines/modeling/static_modeling.py"),
]
def methods(p):
    t=ast.parse(open(os.path.join(root,p),encoding="utf-8",errors="replace").read())
    out={}
    for n in t.body:
        if isinstance(n,ast.ClassDef):
            out[n.name]=[x.name for x in n.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))]
    return out
for lp,cp in pairs:
    L=methods(lp); C=methods(cp)
    print(f"\n=== {lp}\n    vs {cp}")
    for cls,ms in L.items():
        cms=set().union(*[set(v) for v in C.values()]) if C else set()
        missing=[m for m in ms if m not in cms and not m.startswith('_')]
        print(f"  legacy class {cls}: {len(ms)} methods, {len(missing)} not in current: {missing[:12]}")
    print("  current classes:", list(C))
