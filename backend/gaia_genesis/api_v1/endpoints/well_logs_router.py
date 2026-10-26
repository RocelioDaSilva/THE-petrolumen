from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import structlog

from auth_utils import get_current_active_user
from ...well_logs.las_parser import LASParser

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/parse-las", tags=["Gaia - Well Logs"])
async def parse_las_file(
    file: UploadFile = File(..., description="The .las well log file to upload and parse"),
    current_user=Depends(get_current_active_user),
):
    """
    Uploads and parses a LAS (Log ASCII Standard) well log file.
    Extracts well header metadata, curve definitions, track mappings, depth records, and summary statistics.
    """
    if not file.filename.lower().endswith((".las", ".txt")):
        logger.warning(
            "Uploaded file extension is not .las", filename=file.filename
        )

    try:
        content_bytes = await file.read()
        parsed_data = LASParser.parse_las(content_bytes)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=jsonable_encoder({
                "message": f"Successfully parsed LAS file '{file.filename}'.",
                "filename": file.filename,
                "data": parsed_data,
            }),
        )
    except Exception as e:
        logger.error(
            "Error parsing uploaded LAS file",
            filename=file.filename,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse LAS file '{file.filename}': {str(e)}",
        )
    finally:
        await file.close()
