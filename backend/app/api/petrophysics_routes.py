"""HTTP routes for petrophysical rock typing and machine learning facies classification.

In-repo Training Benchmark Samples:
When no custom training dataset is supplied in the request, the endpoint trains
the Random Forest classifier on 8 calibrated well log records embedded inline below:
  1. Gamma: 35.0 API,  Res: 150.0 ohm-m, Density: 2.65 g/cc, Porosity: 0.08  -> Facies: 1 (Clean Sandstone)
  2. Gamma: 40.0 API,  Res: 120.0 ohm-m, Density: 2.62 g/cc, Porosity: 0.12  -> Facies: 1 (Clean Sandstone)
  3. Gamma: 65.0 API,  Res: 45.0 ohm-m,  Density: 2.55 g/cc, Porosity: 0.16  -> Facies: 2 (Shaly Sand)
  4. Gamma: 75.0 API,  Res: 30.0 ohm-m,  Density: 2.50 g/cc, Porosity: 0.18  -> Facies: 2 (Shaly Sand)
  5. Gamma: 115.0 API, Res: 8.0 ohm-m,   Density: 2.40 g/cc, Porosity: 0.22  -> Facies: 3 (Marine Shale)
  6. Gamma: 130.0 API, Res: 4.5 ohm-m,   Density: 2.35 g/cc, Porosity: 0.25  -> Facies: 3 (Marine Shale)
  7. Gamma: 20.0 API,  Res: 250.0 ohm-m, Density: 2.71 g/cc, Porosity: 0.05  -> Facies: 4 (Tight Carbonate / Limestone)
  8. Gamma: 25.0 API,  Res: 210.0 ohm-m, Density: 2.68 g/cc, Porosity: 0.07  -> Facies: 4 (Tight Carbonate / Limestone)
"""

from __future__ import annotations

import math
from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from ..engines.petrophysics.facies import predict_facies, train_facies_classifier

router = APIRouter()

# 8 inline labeled well log records representative of typical lithofacies
DEFAULT_LABELED_FACIES_SAMPLES: list[dict[str, Any]] = [
    {"gamma": 35.0, "resistivity": 150.0, "density": 2.65, "porosity": 0.08, "facies": 1},
    {"gamma": 40.0, "resistivity": 120.0, "density": 2.62, "porosity": 0.12, "facies": 1},
    {"gamma": 65.0, "resistivity": 45.0, "density": 2.55, "porosity": 0.16, "facies": 2},
    {"gamma": 75.0, "resistivity": 30.0, "density": 2.50, "porosity": 0.18, "facies": 2},
    {"gamma": 115.0, "resistivity": 8.0, "density": 2.40, "porosity": 0.22, "facies": 3},
    {"gamma": 130.0, "resistivity": 4.5, "density": 2.35, "porosity": 0.25, "facies": 3},
    {"gamma": 20.0, "resistivity": 250.0, "density": 2.71, "porosity": 0.05, "facies": 4},
    {"gamma": 25.0, "resistivity": 210.0, "density": 2.68, "porosity": 0.07, "facies": 4},
]


class FaciesLogRecord(BaseModel):
    gamma: float = Field(
        ...,
        example=45.0,
        description="Gamma Ray log reading in API units.",
    )
    resistivity: float = Field(
        ...,
        example=110.0,
        description="Deep resistivity log reading in ohm-m.",
    )
    density: float = Field(
        ...,
        example=2.63,
        description="Bulk density log reading in g/cm3.",
    )
    porosity: float = Field(
        ...,
        example=0.11,
        description="Neutron or effective porosity fraction (0 to 1).",
    )
    depth: float | None = Field(
        default=None,
        example=2450.5,
        description="Optional measured depth in meters or feet.",
    )

    @model_validator(mode="after")
    def check_finite(self) -> "FaciesLogRecord":
        for val in (self.gamma, self.resistivity, self.density, self.porosity):
            if not math.isfinite(val):
                raise ValueError("Log curve values must be finite numbers.")
        if self.depth is not None and not math.isfinite(self.depth):
            raise ValueError("Depth must be a finite number if provided.")
        return self


class LabeledFaciesLogRecord(FaciesLogRecord):
    facies: int | str = Field(
        ...,
        example=1,
        description="Known lithofacies class identifier or label.",
    )


class FaciesClassifyRequest(BaseModel):
    predict_data: list[FaciesLogRecord] = Field(
        ...,
        min_length=1,
        example=[
            {"gamma": 38.0, "resistivity": 135.0, "density": 2.64, "porosity": 0.10, "depth": 2100.0},
            {"gamma": 125.0, "resistivity": 5.2, "density": 2.38, "porosity": 0.24, "depth": 2101.0},
        ],
        description="Wireline log curves for unlabeled depth intervals to be classified.",
    )
    training_data: list[LabeledFaciesLogRecord] | None = Field(
        default=None,
        example=[
            {"gamma": 35.0, "resistivity": 150.0, "density": 2.65, "porosity": 0.08, "facies": 1},
            {"gamma": 120.0, "resistivity": 6.0, "density": 2.38, "porosity": 0.23, "facies": 3},
        ],
        description=(
            "Optional custom labeled training data. If omitted or empty, 8 inline "
            "calibrated benchmark well log samples are used."
        ),
    )
    n_estimators: int = Field(
        default=100,
        gt=0,
        le=500,
        example=100,
        description="Number of decision trees for the Random Forest classifier.",
    )


class FaciesClassifyResponse(BaseModel):
    facies_predictions: list[int | str]
    classes: list[int | str]
    features_used: list[str]
    training_samples_count: int
    classification_report: dict[str, Any] | None = None


@router.post(
    "/engine/petrophysics/facies/classify",
    tags=["Petrophysics"],
    response_model=FaciesClassifyResponse,
)
def classify_facies(payload: FaciesClassifyRequest) -> FaciesClassifyResponse:
    """Classify lithofacies from well log curves (gamma, resistivity, density, porosity)

    Uses a Random Forest classifier. If custom training data is omitted, 8 in-repo
    benchmark samples covering Sandstone, Shaly Sand, Marine Shale, and Carbonate are utilized.
    """
    features = ["gamma", "resistivity", "density", "porosity"]

    if payload.training_data and len(payload.training_data) >= 2:
        train_dicts = [item.model_dump() for item in payload.training_data]
    else:
        train_dicts = list(DEFAULT_LABELED_FACIES_SAMPLES)

    train_df = pd.DataFrame(train_dicts)
    predict_df = pd.DataFrame([item.model_dump() for item in payload.predict_data])

    try:
        clf, report, _ = train_facies_classifier(
            df=train_df,
            features=features,
            target_col="facies",
            test_size=0.2,
            n_estimators=payload.n_estimators,
        )
        predictions = predict_facies(clf, predict_df, features=features)
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    pred_list: list[int | str] = []
    for p in predictions:
        try:
            val_float = float(p)
            if val_float.is_integer():
                pred_list.append(int(val_float))
            else:
                pred_list.append(val_float)
        except (ValueError, TypeError):
            pred_list.append(str(p))

    classes_list: list[int | str] = []
    for c in clf.classes_:
        try:
            val_float = float(c)
            if val_float.is_integer():
                classes_list.append(int(val_float))
            else:
                classes_list.append(val_float)
        except (ValueError, TypeError):
            classes_list.append(str(c))

    return FaciesClassifyResponse(
        facies_predictions=pred_list,
        classes=classes_list,
        features_used=features,
        training_samples_count=len(train_df),
        classification_report=report,
    )
