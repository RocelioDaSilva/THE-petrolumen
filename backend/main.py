from fastapi import FastAPI, UploadFile, File, HTTPException, Path
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Tuple

from gaia_genesis.reservoir_engineering.data_management import DataUploader, clear_data_store
import pandas as pd

app = FastAPI(
    title="PetroLúmen Backend API",
    description="API for reservoir engineering tasks. NOTE: Current data handling logic is a placeholder for demonstration.",
    version="0.1.0"
)

# Initialize the data uploader instance
# In a real app, this might be managed with dependency injection
data_uploader = DataUploader()

# --- API Helper Functions ---
def dataframe_to_json_serializable(df: pd.DataFrame | None) -> Any:
    """Converts DataFrame to JSON serializable format, handling NaNs."""
    if df is None:
        return None
    # Replace NaN with None (null in JSON) and convert to records
    return df.where(pd.notnull(df), None).to_dict(orient='records')

# --- API Endpoints ---

@app.get("/", tags=["General"])
async def root() -> Dict[str, str]:
    """Root endpoint providing a welcome message."""
    return {"message": "Welcome to the PetroLúmen Backend API. Current data management is for demonstration."}

@app.get("/health", tags=["General"])
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}

@app.post("/api/v1/wells/{well_name}/data", tags=["Well Data Management"])
async def upload_well_data(
    well_name: str = Path(..., title="The name of the well", min_length=1),
    files: List[UploadFile] = File(..., description="List of CSV files to upload for the well")
) -> JSONResponse:
    """
    Uploads CSV data files for a specific well.
    The data is stored in-memory for this demonstration.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files were provided.")

    csv_files_content: List[Tuple[str, str]] = []
    for file in files:
        if file.content_type != "text/csv": # Basic MIME type check
            raise HTTPException(status_code=400, detail=f"File '{file.filename}' is not a CSV. Found: {file.content_type}")
        try:
            content_bytes = await file.read()
            content_str = content_bytes.decode('utf-8') # Assuming UTF-8, adjust if needed
            csv_files_content.append((file.filename, content_str))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading file {file.filename}: {str(e)}")
        finally:
            await file.close()

    success, message, data = data_uploader.load_well_data(well_name, csv_files_content)

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return JSONResponse(content={
        "message": message,
        "well_name": well_name,
        "files_processed": [f.filename for f in files],
        "data_preview_first_5_rows": dataframe_to_json_serializable(data.head(5) if data is not None else None) # type: ignore
    })

@app.get("/api/v1/wells/{well_name}/preview", tags=["Well Data Management"])
async def get_well_data_preview(
    well_name: str = Path(..., title="The name of the well", min_length=1),
    n_rows: int = 5
) -> JSONResponse:
    """Retrieves a preview (first N rows) of the data for a specific well."""
    preview_df = data_uploader.get_data_preview(well_name, n_rows)
    if preview_df is None:
        raise HTTPException(status_code=404, detail=f"Data for well '{well_name}' not found.")
    return JSONResponse(content={
        "well_name": well_name,
        "preview": dataframe_to_json_serializable(preview_df)
    })

@app.get("/api/v1/wells/{well_name}/statistics", tags=["Well Data Management"])
async def get_well_data_statistics(
    well_name: str = Path(..., title="The name of the well", min_length=1)
) -> JSONResponse:
    """Retrieves descriptive statistics for the data of a specific well."""
    stats = data_uploader.get_well_statistics(well_name)
    if stats is None:
        raise HTTPException(status_code=404, detail=f"Data for well '{well_name}' not found.")
    return JSONResponse(content={
        "well_name": well_name,
        "statistics": stats # Already a dict
    })

@app.get("/api/v1/wells", tags=["Well Data Management"])
async def list_wells_with_data() -> JSONResponse:
    """Lists all wells for which data has been loaded into the in-memory store."""
    wells = data_uploader.list_loaded_wells()
    return JSONResponse(content={"wells": wells})

@app.delete("/api/v1/admin/clear_all_well_data", tags=["Admin"])
async def admin_clear_all_data() -> JSONResponse:
    """
    ADMIN Endpoint: Clears all well data from the in-memory store.
    Use with caution.
    """
    clear_data_store()
    return JSONResponse(content={"message": "All in-memory well data has been cleared."})


if __name__ == "__main__":
    import uvicorn
    # This allows running the app with `python main.py` for development
    # The command `uvicorn main:app --reload` is standard for FastAPI development
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
