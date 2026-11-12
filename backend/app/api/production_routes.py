"""HTTP routes for production engineering calculation engines."""

from __future__ import annotations

import csv
import datetime
import io
import logging
import math
import re
from typing import Any, BinaryIO

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import Field, model_validator
from sqlalchemy.exc import SQLAlchemyError
from starlette.concurrency import run_in_threadpool

from .base import APIModel as BaseModel

from ..engines.production.economic_analysis import EconomicAnalysis
from ..persistence.database import DatabaseManager
from ..persistence.dependencies import get_current_user, get_database_manager

router = APIRouter()
logger = logging.getLogger(__name__)

MAX_PRODUCTION_CSV_BYTES = 10 * 1024 * 1024
MAX_PRODUCTION_CSV_ROWS = 50_000
MAX_CSV_VALIDATION_ERRORS = 100
_PRODUCTION_RATE_COLUMNS = ("oil_rate", "gas_rate", "water_rate")


class ProductionCsvImportResponse(BaseModel):
    rows_received: int
    rows_imported: int
    rows_skipped_duplicates: int
    wells_created: int


class ProductionWellResponse(BaseModel):
    id: int
    name: str
    field: str | None
    latitude: float | None
    longitude: float | None


class ProductionTrendPoint(BaseModel):
    date: str
    oil_rate: float
    gas_rate: float
    water_rate: float


class ProductionWellLatestResponse(BaseModel):
    well_id: int
    well_name: str
    date: str
    oil_rate: float | None
    gas_rate: float | None
    water_rate: float | None


class ProductionOverviewResponse(BaseModel):
    series: list[ProductionTrendPoint]
    latest_import_at: str | None
    latest_well_rates: list[ProductionWellLatestResponse]


@router.get(
    "/production/wells",
    tags=["Production"],
    response_model=list[ProductionWellResponse],
)
def list_production_wells(
    user: dict[str, Any] = Depends(get_current_user),
    database: DatabaseManager = Depends(get_database_manager),
) -> list[ProductionWellResponse]:
    """List only wells owned by the authenticated user."""
    return [
        ProductionWellResponse(**well)
        for well in database.list_wells(owner_id=user["id"])
    ]


@router.get(
    "/production/overview",
    tags=["Production"],
    response_model=ProductionOverviewResponse,
)
def get_production_overview(
    user: dict[str, Any] = Depends(get_current_user),
    database: DatabaseManager = Depends(get_database_manager),
) -> ProductionOverviewResponse:
    """Return date aggregates and latest rates for the authenticated user's wells."""
    return ProductionOverviewResponse(
        **database.get_production_overview(owner_id=user["id"])
    )


@router.post(
    "/production/import/csv",
    tags=["Production"],
    response_model=ProductionCsvImportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def import_production_csv(
    file: UploadFile = File(...),
    user: dict[str, Any] = Depends(get_current_user),
    database: DatabaseManager = Depends(get_database_manager),
) -> ProductionCsvImportResponse:
    """Validate and import an authenticated production-history CSV."""
    if not (file.filename or "").lower().endswith(".csv"):
        await file.close()
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Upload a .csv file.",
        )

    try:
        records = await run_in_threadpool(_read_and_parse_production_csv, file.file)
    finally:
        await file.close()

    try:
        imported, duplicates, wells_created = await run_in_threadpool(
            database.import_production_records, user["id"], records
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except SQLAlchemyError as exc:
        logger.exception("Could not import production CSV data.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Production data could not be saved; no rows were imported.",
        ) from exc

    return ProductionCsvImportResponse(
        rows_received=len(records),
        rows_imported=imported,
        rows_skipped_duplicates=duplicates,
        wells_created=wells_created,
    )


def _read_and_parse_production_csv(file_obj: BinaryIO) -> list[dict[str, Any]]:
    content = bytearray()
    while True:
        chunk = file_obj.read(64 * 1024)
        if not chunk:
            break
        content.extend(chunk)
        if len(content) > MAX_PRODUCTION_CSV_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=(
                    "Production CSV exceeds the 10 MB upload limit."
                ),
            )

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="CSV must use UTF-8 encoding.",
        ) from exc

    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    try:
        raw_headers = next(
            row for row in reader if any(value.strip() for value in row)
        )
    except StopIteration as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="CSV is empty.",
        ) from exc
    except csv.Error as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not parse CSV header: {exc}",
        ) from exc

    headers = [header.strip().lower() for header in raw_headers]
    if any(not header for header in headers) or len(headers) != len(set(headers)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="CSV headers must be non-empty and unique.",
        )

    missing_headers = {"well_name", "date"} - set(headers)
    if missing_headers:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "CSV is missing required columns: "
                + ", ".join(sorted(missing_headers))
                + "."
            ),
        )
    if not set(_PRODUCTION_RATE_COLUMNS).intersection(headers):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "CSV must include at least one rate column: "
                + ", ".join(_PRODUCTION_RATE_COLUMNS)
                + "."
            ),
        )

    records: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    total_errors = 0

    def add_error(row_number: int, message: str) -> None:
        nonlocal total_errors
        total_errors += 1
        if len(errors) < MAX_CSV_VALIDATION_ERRORS:
            errors.append({"row": row_number, "message": message})

    data_row_count = 0
    try:
        for values in reader:
            if not any(value.strip() for value in values):
                continue
            data_row_count += 1
            row_number = data_row_count + 1
            if data_row_count > MAX_PRODUCTION_CSV_ROWS:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=(
                        f"CSV exceeds the {MAX_PRODUCTION_CSV_ROWS:,}-row limit."
                    ),
                )
            if len(values) != len(headers):
                add_error(row_number, "Column count does not match the CSV header.")
                continue

            row = {
                header: value.strip()
                for header, value in zip(headers, values, strict=True)
            }
            well_name = row["well_name"]
            date_text = row["date"]
            row_errors: list[str] = []
            if not well_name:
                row_errors.append("well_name is required.")
            elif len(well_name) > 120:
                row_errors.append("well_name must be at most 120 characters.")

            production_date: datetime.date | None = None
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_text):
                row_errors.append("date must use YYYY-MM-DD format.")
            else:
                try:
                    production_date = datetime.date.fromisoformat(date_text)
                except ValueError:
                    row_errors.append("date is not a valid calendar date.")

            rates: dict[str, float | None] = {}
            for column in _PRODUCTION_RATE_COLUMNS:
                value = row.get(column, "")
                if not value:
                    rates[column] = None
                    continue
                try:
                    rate = float(value)
                except ValueError:
                    row_errors.append(f"{column} must be a finite non-negative number.")
                    continue
                if not math.isfinite(rate) or rate < 0:
                    row_errors.append(f"{column} must be a finite non-negative number.")
                    continue
                rates[column] = rate

            if not any(rate is not None for rate in rates.values()):
                row_errors.append("At least one production rate is required per row.")

            if row_errors:
                for message in row_errors:
                    add_error(row_number, message)
                continue

            records.append(
                {
                    "well_name": well_name,
                    "date": production_date,
                    **rates,
                }
            )
    except csv.Error as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not parse CSV near row {reader.line_num}: {exc}",
        ) from exc

    if total_errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Production CSV contains invalid rows.",
                "errors": errors,
                "total_errors": total_errors,
                "errors_truncated": total_errors > len(errors),
            },
        )
    if not records:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="CSV contains no production records.",
        )
    return records


class ProductionEconomicsRequest(BaseModel):
    oil_price: float = Field(
        ...,
        ge=0.0,
        example=70.0,
        description="Oil price in $/bbl (must be non-negative).",
    )
    gas_price: float = Field(
        ...,
        ge=0.0,
        example=3.0,
        description="Gas price in $/Mscf (must be non-negative).",
    )
    discount_rate: float = Field(
        ...,
        gt=-100.0,
        example=10.0,
        description="Annual discount rate percentage (e.g. 10.0 for 10%).",
    )
    project_life: int = Field(
        ...,
        gt=0,
        example=5,
        description="Project life in years (positive integer).",
    )
    capex: dict[str, float] = Field(
        ...,
        example={"drilling": 1000000.0, "facilities": 500000.0},
        description="Initial capital expenditure breakdown (year zero, non-negative).",
    )
    opex: dict[str, float] = Field(
        ...,
        example={"fixed_opex": 50000.0, "variable_opex": 25000.0},
        description="Annual operating expenditure breakdown (non-negative).",
    )
    tax_rate: float = Field(
        default=0.34,
        ge=0.0,
        le=1.0,
        example=0.34,
        description="Corporate income tax rate as a fraction between 0.0 and 1.0.",
    )
    water_disposal_cost_per_bbl: float = Field(
        default=0.0,
        ge=0.0,
        example=1.5,
        description="Water disposal cost per barrel of produced water.",
    )
    oil_production: list[float] = Field(
        ...,
        example=[100000.0, 80000.0, 60000.0, 45000.0, 30000.0],
        description="Annual oil production volumes in bbl/year.",
    )
    gas_production: list[float] = Field(
        ...,
        example=[500000.0, 400000.0, 300000.0, 200000.0, 100000.0],
        description="Annual gas production volumes in Mscf/year.",
    )
    water_production: list[float] = Field(
        ...,
        example=[20000.0, 30000.0, 40000.0, 50000.0, 60000.0],
        description="Annual water production volumes in bbl/year.",
    )

    @model_validator(mode="after")
    def validate_volumes_length(self) -> "ProductionEconomicsRequest":
        life = self.project_life
        for name, values in (
            ("oil_production", self.oil_production),
            ("gas_production", self.gas_production),
            ("water_production", self.water_production),
        ):
            if len(values) != life:
                raise ValueError(
                    f"{name} must contain exactly {life} annual volumes to match project_life."
                )
            if any(not math.isfinite(v) or v < 0.0 for v in values):
                raise ValueError(f"{name} volumes must be finite and non-negative.")
        return self


class CashFlowRevenue(BaseModel):
    oil: list[float]
    gas: list[float]
    total: list[float]


class CashFlowCosts(BaseModel):
    opex: list[float]
    water_disposal: list[float]
    total: list[float]
    initial_capex: float


class CashFlowDetails(BaseModel):
    revenue: CashFlowRevenue
    costs: CashFlowCosts
    depreciation: list[float]
    ebitda: list[float]
    ebit: list[float]
    taxes: list[float]
    net_income: list[float]
    operating_cash_flow: list[float]
    cash_flow: list[float]


class ProductionEconomicsResponse(BaseModel):
    npv: float
    irr: float | None
    payout: float | None
    roi: float | None
    cashflow: list[float]
    cumulative_cashflow: list[float]
    cash_flow_details: CashFlowDetails


@router.post(
    "/engine/production/economics",
    tags=["Production"],
    response_model=ProductionEconomicsResponse,
)
def calculate_production_economics(
    payload: ProductionEconomicsRequest,
) -> ProductionEconomicsResponse:
    """Evaluate annual field production economics: NPV, IRR, payout, and cash flows."""
    analysis = EconomicAnalysis()
    try:
        analysis.set_economic_parameters(
            oil_price=payload.oil_price,
            gas_price=payload.gas_price,
            discount_rate=payload.discount_rate,
            project_life=payload.project_life,
            capex=payload.capex,
            opex=payload.opex,
            tax_rate=payload.tax_rate,
            water_disposal_cost_per_bbl=payload.water_disposal_cost_per_bbl,
        )
        cf = analysis.calculate_cash_flow(
            oil_production=payload.oil_production,
            gas_production=payload.gas_production,
            water_production=payload.water_production,
        )
        npv = analysis.calculate_npv()

        irr: float | None = None
        try:
            irr = float(analysis.calculate_irr())
        except ValueError:
            irr = None

        payout: float | None = None
        try:
            payout = float(analysis.calculate_payback())
        except ValueError:
            payout = None

        roi: float | None = None
        try:
            roi = float(analysis.calculate_roi())
        except ValueError:
            roi = None

    except (ValueError, KeyError, ArithmeticError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    raw_cashflow = [float(x) for x in cf["cash_flow"]]
    cum_cashflow: list[float] = []
    current_sum = 0.0
    for flow in raw_cashflow:
        current_sum += flow
        cum_cashflow.append(current_sum)

    details = CashFlowDetails(
        revenue=CashFlowRevenue(
            oil=[float(x) for x in cf["revenue"]["oil"]],
            gas=[float(x) for x in cf["revenue"]["gas"]],
            total=[float(x) for x in cf["revenue"]["total"]],
        ),
        costs=CashFlowCosts(
            opex=[float(x) for x in cf["costs"]["opex"]],
            water_disposal=[float(x) for x in cf["costs"]["water_disposal"]],
            total=[float(x) for x in cf["costs"]["total"]],
            initial_capex=float(cf["costs"]["initial_capex"]),
        ),
        depreciation=[float(x) for x in cf["depreciation"]],
        ebitda=[float(x) for x in cf["ebitda"]],
        ebit=[float(x) for x in cf["ebit"]],
        taxes=[float(x) for x in cf["taxes"]],
        net_income=[float(x) for x in cf["net_income"]],
        operating_cash_flow=[float(x) for x in cf["operating_cash_flow"]],
        cash_flow=raw_cashflow,
    )

    return ProductionEconomicsResponse(
        npv=float(npv),
        irr=irr,
        payout=payout,
        roi=roi,
        cashflow=raw_cashflow,
        cumulative_cashflow=cum_cashflow,
        cash_flow_details=details,
    )
