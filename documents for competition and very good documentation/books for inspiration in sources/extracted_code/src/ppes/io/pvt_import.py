"""PVT import from CSV/XLSX."""
from pathlib import Path
import pandas as pd
import numpy as np
from ..ch07_forecast import PVTTable

REQUIRED = {"pressure_psia", "rs_scf_stb", "bo_rb_stb"}

def load_pvt(path):
    p = Path(path)
    if p.suffix.lower() in (".xlsx", ".xls"):
        df = pd.read_excel(p)
    elif p.suffix.lower() == ".csv":
        df = pd.read_csv(p)
    else:
        raise ValueError(f"Unsupported format: {p.suffix}")
    missing = REQUIRED - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    n = len(df)
    return PVTTable(
        pressures=df["pressure_psia"].values,
        Rs=df["rs_scf_stb"].values,
        Bo=df["bo_rb_stb"].values,
        Bg=df.get("bg_rb_scf", pd.Series([0.0]*n)).values,
        mu_o=df.get("mu_cp", pd.Series([1.0]*n)).values,
        kro=df.get("kro", pd.Series([1.0]*n)).values,
        krg=df.get("krg", pd.Series([0.0]*n)).values,
    )

def validate_pvt(t):
    w = []
    if np.any(np.diff(t.pressures) < 0):
        w.append("Pressures must be monotonic")
    if np.any(t.Bo <= 0):
        w.append("B_o must be positive")
    if np.any(t.Rs < 0):
        w.append("R_s must be non-negative")
    return w
