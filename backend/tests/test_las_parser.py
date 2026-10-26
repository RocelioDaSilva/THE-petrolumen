import io
import pytest
from gaia_genesis.well_logs.las_parser import LASParser

SAMPLE_LAS_CONTENT = """~VERSION INFORMATION
 VERS.                  2.0 : CWLS LOG ASCII STANDARD -VERSION 2.0
 WRAP.                   NO : ONE LINE PER DEPTH STEP
~WELL INFORMATION
 STRT.M             1000.00 : START DEPTH
 STOP.M             1005.00 : STOP DEPTH
 STEP.M                1.00 : STEP
 NULL.              -999.25 : NULL VALUE
 WELL.             ALPHA-01 : WELL NAME
 COMP.          PETROLUMEN : COMPANY
 FLD.           GAIA FIELD : FIELD
 API.       42-123-45678-00 : API NUMBER
~CURVE INFORMATION
 DEPT.M                      : DEPTH
 GR.API                      : GAMMA RAY
 ILD.OHMM                    : DEEP INDUCTION
 NPHI.V/V                    : NEUTRON POROSITY
 RHOB.G/C3                   : BULK DENSITY
~PARAMETER INFORMATION
 BHT .DEG C           85.00 : BOTTOM HOLE TEMP
~ASCII LOG DATA
1000.00   45.2   12.5   0.18   2.45
1001.00   52.0   15.0   0.20   2.42
1002.00  -999.25 18.2   0.22   2.38
1003.00   68.5   -999.25 0.19  2.44
1004.00   75.0   22.0  -999.25 2.40
1005.00   80.0   25.0   0.15  -999.25
"""


def test_las_parser_structured_output():
    parsed = LASParser.parse_las(SAMPLE_LAS_CONTENT)

    assert parsed["well_name"] == "ALPHA-01"
    assert parsed["metadata"]["FLD"]["value"] == "GAIA FIELD"
    assert parsed["metadata"]["COMP"]["value"] == "PETROLUMEN"

    # Curves
    curves = parsed["curves"]
    assert "DEPT" in curves or "DEPTH" in curves
    assert "GR" in curves
    assert "ILD" in curves
    assert "NPHI" in curves
    assert "RHOB" in curves

    # Check null conversion (NaNs replaced with None)
    gr_data = curves["GR"]["data"]
    assert gr_data[0] == 45.2
    assert gr_data[2] is None  # -999.25 null value converted to None

    # Track categorization
    tracks = parsed["tracks"]
    assert "track1" in tracks
    assert "track2" in tracks
    assert "track3" in tracks

    # Summary
    summary = parsed["summary"]
    assert summary["well_name"] == "ALPHA-01"
    assert summary["curve_count"] == 5
    assert summary["record_count"] == 6


def test_las_parser_endpoint_and_main_upload(client, user_auth_headers):
    files = {"file": ("test_well.las", io.BytesIO(SAMPLE_LAS_CONTENT.encode("utf-8")), "text/plain")}

    # Test /api/v1/gaia/well-logs/parse-las
    response = client.post(
        "/api/v1/gaia/well-logs/parse-las",
        files=files,
        headers=user_auth_headers,
    )
    assert response.status_code == 200
    json_data = response.json()
    assert "data" in json_data
    assert json_data["data"]["well_name"] == "ALPHA-01"

    # Test /api/v1/wells/{well_id}/upload-las
    files2 = {"file": ("test_well.las", io.BytesIO(SAMPLE_LAS_CONTENT.encode("utf-8")), "text/plain")}
    response2 = client.post(
        "/api/v1/wells/WELL-999/upload-las",
        files=files2,
        headers=user_auth_headers,
    )
    assert response2.status_code == 200
    json_data2 = response2.json()
    assert json_data2["well_id"] == "WELL-999"
    assert json_data2["summary"]["curve_count"] == 5
