import io
from typing import Dict, List, Any, Optional, Union
import lasio
import numpy as np
import pandas as pd
import structlog

logger = structlog.get_logger(__name__)


class LASParser:
    """
    Parser utility for reading, extracting, and structuring LAS (Log ASCII Standard) file data.
    Uses `lasio` under the hood and provides structured JSON-serializable output for PetroLúmen.
    """

    # Standard log curve categorization
    TRACK_MAPPINGS = {
        "track1": {
            "name": "Lithology & Caliper",
            "keywords": ["GR", "SGR", "CGR", "CALI", "CAL", "BS", "SP", "POTA", "THOR", "URAN"],
        },
        "track2": {
            "name": "Resistivity",
            "keywords": ["ILD", "ILM", "LLD", "LLS", "LL8", "SFL", "RT", "RES", "AT90", "AT10", "AHT90"],
            "scale": "logarithmic",
        },
        "track3": {
            "name": "Porosity & Density",
            "keywords": ["NPHI", "RHOB", "PHIE", "PHIT", "DT", "DPHI", "TNPH", "PE", "PEF"],
        },
    }

    @classmethod
    def parse_las(
        cls, file_input: Union[str, bytes, io.StringIO, io.BytesIO]
    ) -> Dict[str, Any]:
        """
        Parses a LAS file from string, bytes, or file-like stream.

        Returns a structured dictionary with:
        - metadata: Well header details (well name, company, field, API, start/stop/step depth, etc.)
        - curves: Dict of curves with units, descriptions, and data arrays (NaN -> None)
        - tracks: Mapped track configurations for frontend rendering
        - records: Row-based depth records (JSON-serializable)
        - summary: Summary metrics (start depth, stop depth, step, record count, curve list)
        """
        las = cls._load_las_object(file_input)

        well_name = cls._get_header_item(las, "WELL", default="Unknown Well")
        metadata = cls._extract_metadata(las)
        curves_info = cls._extract_curves(las)
        tracks_config = cls._categorize_tracks(list(curves_info.keys()))
        records = cls._extract_records(las)
        summary = cls._generate_summary(las, well_name, curves_info, records)

        return {
            "well_name": well_name,
            "metadata": metadata,
            "curves": curves_info,
            "tracks": tracks_config,
            "records": records,
            "summary": summary,
        }

    @classmethod
    def _load_las_object(
        cls, file_input: Union[str, bytes, io.StringIO, io.BytesIO]
    ) -> lasio.LASFile:
        """Loads lasio.LASFile from various input types."""
        if isinstance(file_input, bytes):
            content_str = file_input.decode("utf-8", errors="ignore")
            return lasio.read(io.StringIO(content_str))
        elif isinstance(file_input, str):
            if "\n" in file_input or "~" in file_input:
                return lasio.read(io.StringIO(file_input))
            else:
                return lasio.read(file_input)
        elif isinstance(file_input, io.BytesIO):
            content_str = file_input.getvalue().decode("utf-8", errors="ignore")
            return lasio.read(io.StringIO(content_str))
        elif isinstance(file_input, io.StringIO):
            return lasio.read(file_input)
        else:
            raise ValueError(f"Unsupported LAS file input type: {type(file_input)}")

    @classmethod
    def _get_header_item(
        cls, las: lasio.LASFile, mnemonic: str, default: str = ""
    ) -> str:
        """Gets value of a mnemonic from well header section."""
        try:
            for item in las.well:
                if item.mnemonic.upper() == mnemonic.upper():
                    if item.value is not None:
                        val_str = str(item.value).strip()
                        if val_str:
                            return val_str
        except Exception:
            pass
        return default

    @classmethod
    def _extract_metadata(cls, las: lasio.LASFile) -> Dict[str, Dict[str, Any]]:
        """Extracts well header metadata into dictionary."""
        metadata: Dict[str, Dict[str, Any]] = {}

        # Well section
        for item in las.well:
            val = item.value
            if isinstance(val, float) and (np.isnan(val) or np.isinf(val)):
                val = None
            metadata[item.mnemonic] = {
                "value": val,
                "unit": item.unit if item.unit else "",
                "description": item.descr if item.descr else "",
            }

        # Parameters section if present
        if hasattr(las, "params") and las.params:
            for item in las.params:
                val = item.value
                if isinstance(val, float) and (np.isnan(val) or np.isinf(val)):
                    val = None
                metadata[f"PARAM_{item.mnemonic}"] = {
                    "value": val,
                    "unit": item.unit if item.unit else "",
                    "description": item.descr if item.descr else "",
                }

        return metadata

    @classmethod
    def _extract_curves(cls, las: lasio.LASFile) -> Dict[str, Dict[str, Any]]:
        """Extracts curves, replacing NaN/Inf with None."""
        curves: Dict[str, Dict[str, Any]] = {}
        for curve in las.curves:
            mnemonic = curve.mnemonic.upper()
            data_raw = las[curve.mnemonic]

            # Convert numpy array / series replacing NaN or Inf with None
            clean_data = [
                None
                if (val is None or np.isnan(val) or np.isinf(val))
                else float(val)
                for val in data_raw
            ]

            curves[mnemonic] = {
                "mnemonic": mnemonic,
                "unit": curve.unit if curve.unit else "",
                "description": curve.descr if curve.descr else "",
                "data": clean_data,
            }
        return curves

    @classmethod
    def _categorize_tracks(cls, curve_mnemonics: List[str]) -> Dict[str, Any]:
        """Categorizes curve mnemonics into standard multi-track display groups."""
        mnemonics_upper = [m.upper() for m in curve_mnemonics]
        tracks: Dict[str, Any] = {
            "track1": {
                "title": "Track 1: Gamma Ray & Caliper",
                "curves": [],
            },
            "track2": {
                "title": "Track 2: Resistivity (Log Scale)",
                "curves": [],
                "scale": "logarithmic",
            },
            "track3": {
                "title": "Track 3: Porosity & Density",
                "curves": [],
            },
            "other": {
                "title": "Other Curves",
                "curves": [],
            },
        }

        # Find depth curve
        depth_mnemonic = None
        for m in mnemonics_upper:
            if m in ["DEPTH", "DEPT", "DEP"]:
                depth_mnemonic = m
                break

        assigned_curves = set()
        if depth_mnemonic:
            assigned_curves.add(depth_mnemonic)

        for track_id, config in cls.TRACK_MAPPINGS.items():
            keywords = config["keywords"]
            for m in mnemonics_upper:
                if m in assigned_curves:
                    continue
                if any(kw in m for kw in keywords):
                    tracks[track_id]["curves"].append(m)
                    assigned_curves.add(m)

        # Unassigned curves go to 'other'
        for m in mnemonics_upper:
            if m not in assigned_curves:
                tracks["other"]["curves"].append(m)

        return tracks

    @classmethod
    def _extract_records(cls, las: lasio.LASFile) -> List[Dict[str, Any]]:
        """Converts lasio DataFrame into JSON-serializable list of row dicts."""
        try:
            df = las.df().reset_index()
            # Replace NaN/inf with None
            records = []
            for _, row in df.iterrows():
                row_dict = {}
                for col, val in row.items():
                    if pd.isna(val) or (isinstance(val, float) and (np.isnan(val) or np.isinf(val))):
                        row_dict[str(col)] = None
                    else:
                        row_dict[str(col)] = float(val) if isinstance(val, (int, float, np.number)) else str(val)
                records.append(row_dict)
            return records
        except Exception as e:
            logger.warning("Failed to convert LAS dataframe to records", error=str(e))
            return []

    @classmethod
    def _generate_summary(
        cls,
        las: lasio.LASFile,
        well_name: str,
        curves: Dict[str, Dict[str, Any]],
        records: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generates summary statistics and information for the LAS file."""
        strt = cls._get_header_item(las, "STRT")
        stop = cls._get_header_item(las, "STOP")
        step = cls._get_header_item(las, "STEP")
        null_val = cls._get_header_item(las, "NULL")

        return {
            "well_name": well_name,
            "start_depth": float(strt) if strt and strt.replace(".", "", 1).replace("-", "", 1).isdigit() else strt,
            "stop_depth": float(stop) if stop and stop.replace(".", "", 1).replace("-", "", 1).isdigit() else stop,
            "step": float(step) if step and step.replace(".", "", 1).replace("-", "", 1).isdigit() else step,
            "null_value": null_val,
            "curve_count": len(curves),
            "record_count": len(records),
            "curve_list": list(curves.keys()),
        }
