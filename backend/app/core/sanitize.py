"""PVT Input Sanitization & Validation Engine

Enforces strict scientific bounds, prevents division-by-zero,
and ensures unit consistency.
Ported from src/lib/pvt/sanitize.ts.
"""

from __future__ import annotations

import math
import re
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict

PVTUnitSystem = Literal["field", "metric"]


class ValidatedPVTInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pressure: float  # psia
    temperature: float  # °F
    volume: float | None = None  # bbl
    gor: float  # scf/STB
    apiGravity: float  # °API
    gasGravity: float  # air = 1.0
    unitSystem: PVTUnitSystem


class SanitizedPVTOk(BaseModel):
    ok: Literal[True] = True
    value: ValidatedPVTInput


class SanitizedPVTErr(BaseModel):
    ok: Literal[False] = False
    errors: list[str]


SanitizedPVTResult = SanitizedPVTOk | SanitizedPVTErr

_STRICT_NUMBER_REGEX = re.compile(r"^[+-]?(?:\d+\.?\d*|\.\d+)$")


def is_strict_finite_number(val: Any) -> bool:
    """Validates that an input is a genuine finite number (rejects "1e", "1,000", None, NaN, Infinity)."""
    if isinstance(val, bool):
        return False
    if isinstance(val, (int, float)):
        return math.isfinite(val)
    if isinstance(val, str):
        trimmed = val.strip()
        if not trimmed or "," in trimmed:
            return False
        if not _STRICT_NUMBER_REGEX.match(trimmed):
            return False
        try:
            parsed = float(trimmed)
            return math.isfinite(parsed)
        except ValueError:
            return False
    return False


def sanitize_pvt(raw: Any) -> SanitizedPVTResult:
    """Robust sanitizer for PVT inputs. Matches src/lib/pvt/sanitize.ts logic."""
    errors: list[str] = []

    if raw is None or not isinstance(raw, dict):
        return SanitizedPVTErr(errors=["Entrada PVT inválida ou ausente."])

    # 1. Unit System
    unit_system: PVTUnitSystem = "field"
    raw_unit_system = raw.get("unitSystem")
    if raw_unit_system in ("metric", "field"):
        unit_system = raw_unit_system
    elif raw_unit_system is not None:
        errors.append(f"Sistema de unidades inválido: '{raw_unit_system}'. Use 'field' ou 'metric'.")

    # 2. Pressure check (fail loudly on <= 0, no silent clamp)
    raw_pressure = raw.get("pressure")
    if not is_strict_finite_number(raw_pressure):
        errors.append("Pressão deve ser um valor numérico válido.")
    else:
        p = float(raw_pressure)
        if p <= 0:
            unit_label = "kPa" if unit_system == "metric" else "psia"
            errors.append(f"Pressão deve ser estritamente positiva (> 0). Valor fornecido: {p} {unit_label}.")
        elif unit_system == "field" and (p < 14.7 or p > 25000):
            errors.append(f"Pressão de reservatório fora da faixa operacional física (14.7 - 25,000 psia). Valor: {p}")

    # 3. Temperature check (below absolute zero check)
    raw_temp = raw.get("temperature")
    if not is_strict_finite_number(raw_temp):
        errors.append("Temperatura deve ser um valor numérico válido.")
    else:
        t = float(raw_temp)
        if unit_system == "field" and t <= -459.67:
            errors.append(f"Temperatura ({t}°F) está abaixo do zero absoluto (-459.67°F).")
        elif unit_system == "metric" and t <= -273.15:
            errors.append(f"Temperatura ({t}°C) está abaixo do zero absoluto (-273.15°C).")
        elif unit_system == "field" and (t < 32 or t > 500):
            errors.append(f"Temperatura de reservatório fora da faixa operacional plausível (32 - 500°F). Valor: {t}")

    # 4. Gas Specific Gravity (air = 1.0)
    raw_gg = raw.get("gasGravity")
    if raw_gg is not None and not is_strict_finite_number(raw_gg):
        errors.append("Densidade relativa do gás (gammaG) deve ser um número.")
    elif raw_gg is not None:
        gg = float(raw_gg)
        if gg < 0.5 or gg > 2.0:
            errors.append(f"Densidade relativa do gás fora dos limites naturais de hidrocarbonetos (0.5 a 2.0). Valor: {gg}")

    # 5. Oil API Gravity
    raw_api = raw.get("apiGravity")
    if raw_api is not None and not is_strict_finite_number(raw_api):
        errors.append("Grau API deve ser um número válido.")
    elif raw_api is not None:
        api = float(raw_api)
        if api <= 0 or api > 100:
            errors.append(f"Grau API do óleo deve estar entre 0° e 100° API. Valor: {api}")

    # 6. GOR (Solution Gas-Oil Ratio)
    raw_gor = raw.get("gor")
    if raw_gor is not None and not is_strict_finite_number(raw_gor):
        errors.append("Razão Gás-Óleo (GOR) deve ser um número válido.")
    elif raw_gor is not None:
        gor = float(raw_gor)
        if gor < 0:
            errors.append(f"GOR não pode ser negativo. Valor: {gor}")

    if errors:
        return SanitizedPVTErr(errors=errors)

    raw_vol = raw.get("volume")
    volume_val = float(raw_vol) if (raw_vol is not None and is_strict_finite_number(raw_vol)) else None

    return SanitizedPVTOk(
        value=ValidatedPVTInput(
            pressure=float(raw_pressure),
            temperature=float(raw_temp),
            volume=volume_val,
            gor=float(raw_gor) if raw_gor is not None else 600.0,
            apiGravity=float(raw_api) if raw_api is not None else 35.0,
            gasGravity=float(raw_gg) if raw_gg is not None else 0.72,
            unitSystem=unit_system,
        )
    )


# Alias function name matching TypeScript camelCase export
sanitizePVT = sanitize_pvt
