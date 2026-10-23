import uuid
import datetime
import logging
import numpy as np
from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Path
from pydantic import BaseModel
import structlog

from gaia_genesis.core.database_manager import DatabaseManager
from gaia_genesis.core.database_models import Job
from auth_utils import get_current_active_user, UserResponse

logger = structlog.get_logger(__name__)

router = APIRouter()


class JobResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None


@router.get("/{job_id}", response_model=JobResponse, tags=["Jobs"])
async def get_job_status(
    job_id: str = Path(..., title="The UUID of the job"),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """Retrieves the status and result of a job. Enforces owner-only access."""
    db_manager = DatabaseManager.get_instance()
    session = db_manager.get_session()
    try:
        try:
            job_uuid = uuid.UUID(job_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job_id format"
            )

        job = session.query(Job).filter(Job.id == job_uuid).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
            )

        if str(job.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this job",
            )

        return JobResponse(
            job_id=str(job.id),
            status=job.status,
            result=job.result,
            error=job.error,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )
    finally:
        session.close()


def run_flowsim_task(job_id: str, simulator, end_time: float, dt: float):
    """Background task function to execute flow simulation."""
    db_manager = DatabaseManager.get_instance()
    session = db_manager.get_session()
    try:
        job_uuid = uuid.UUID(job_id)
        job = session.query(Job).filter(Job.id == job_uuid).first()
        if not job:
            logger.error(f"Background task: Job {job_id} not found.")
            return

        job.status = "running"
        job.updated_at = datetime.datetime.now(datetime.timezone.utc)
        session.commit()

        # Execute heavy computation
        simulator.run_simulation(end_time, dt)

        sim_status = simulator.simulation_results.get("status", "Unknown")
        if sim_status == "Failed: Singular matrix":
            raise ValueError(
                "Simulation failed due to singular matrix. Check parameters or boundary conditions."
            )

        pressures_vs_time = simulator.simulation_results.get("pressures_vs_time", [])
        block0_pressures = (
            [
                p_step[0]
                for p_step in pressures_vs_time
                if isinstance(p_step, (np.ndarray, list)) and len(p_step) > 0
            ]
            if pressures_vs_time
            else []
        )
        time_array_list = simulator.simulation_results.get(
            "time_array", np.array([])
        ).tolist()

        result_payload = {
            "time_steps": time_array_list,
            "pressure_at_block": {0: block0_pressures},
            "status": sim_status,
        }

        job = session.query(Job).filter(Job.id == job_uuid).first()
        if job:
            job.status = "completed"
            job.result = result_payload
            job.updated_at = datetime.datetime.now(datetime.timezone.utc)
            session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error in flowsim background task for job {job_id}: {e}", exc_info=True)
        try:
            job = session.query(Job).filter(Job.id == uuid.UUID(job_id)).first()
            if job:
                job.status = "failed"
                job.error = str(e)
                job.updated_at = datetime.datetime.now(datetime.timezone.utc)
                session.commit()
        except Exception as inner_e:
            logger.error(f"Failed to update failed job status for {job_id}: {inner_e}")
    finally:
        session.close()


def run_prediction_train_task(
    job_id: str, predictor, records: list, target_column: str, feature_columns: list
):
    """Background task function to execute AI model training."""
    import pandas as pd

    db_manager = DatabaseManager.get_instance()
    session = db_manager.get_session()
    try:
        job_uuid = uuid.UUID(job_id)
        job = session.query(Job).filter(Job.id == job_uuid).first()
        if not job:
            logger.error(f"Background task: Job {job_id} not found.")
            return

        job.status = "running"
        job.updated_at = datetime.datetime.now(datetime.timezone.utc)
        session.commit()

        df = pd.DataFrame(records)
        if df.empty:
            raise ValueError("No records provided for training.")

        X_train, X_test, y_train, y_test = predictor.prepare_data(
            df, target_column, feature_columns
        )
        predictor.train_models(X_train, y_train, X_test, y_test)

        trained_model_names = list(predictor.models.keys())
        performance = {}
        for name, info in predictor.models.items():
            performance[name] = {
                "r2": float(info.get("test_r2", 0)),
                "rmse": float(info.get("test_rmse", 0)),
            }

        result_payload = {
            "message": "Models trained successfully. Best model selected based on R2 score.",
            "trained_models": trained_model_names,
            "performance": performance,
            "best_model": predictor.best_model,
        }

        job = session.query(Job).filter(Job.id == job_uuid).first()
        if job:
            job.status = "completed"
            job.result = result_payload
            job.updated_at = datetime.datetime.now(datetime.timezone.utc)
            session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error in prediction train background task for job {job_id}: {e}", exc_info=True)
        try:
            job = session.query(Job).filter(Job.id == uuid.UUID(job_id)).first()
            if job:
                job.status = "failed"
                job.error = str(e)
                job.updated_at = datetime.datetime.now(datetime.timezone.utc)
                session.commit()
        except Exception as inner_e:
            logger.error(f"Failed to update failed job status for {job_id}: {inner_e}")
    finally:
        session.close()
