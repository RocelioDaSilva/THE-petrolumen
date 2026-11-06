"""Chapter 1 -- Reference and classifications."""
from pathlib import Path
import pandas as pd

_DATA = Path(__file__).parent / "data"

def load_safety_symbols() -> pd.DataFrame:
    return pd.read_csv(_DATA / "safety_symbols.csv")

def load_wellhead_components() -> pd.DataFrame:
    return pd.read_csv(_DATA / "wellhead_components.csv")

def classify_well(gas_scfd: float, oil_stbd: float) -> str:
    if oil_stbd <= 0: return "gas"
    gor = gas_scfd / oil_stbd
    if gor > 100_000: return "gas"
    if gor > 5_000: return "condensate"
    return "oil"

def classify_drive_mechanism(pm: bool, gc: bool, wd: bool) -> str:
    if wd: return "water_drive"
    if gc: return "gas_cap_drive"
    if not pm: return "dissolved_gas_drive"
    return "unknown"

def well_opening_checklist() -> list[str]:
    return [
        "Check all safety valves and fittings",
        "Light the line heater burner",
        "Ensure surface vessels are open and clear",
        "Crack the master valve until hissing stops",
        "Open the master valve wide",
        "Crack the second master or wing valve",
        "Open the other downstream valves",
        "Read tubing pressure via needle valve",
    ]
