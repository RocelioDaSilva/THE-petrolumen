import uuid
import datetime
import pandas as pd
import numpy as np
import structlog

from gaia_genesis.models import Job
from gaia_genesis.core.database_manager import DatabaseManager
from gaia_genesis.flow_simulation import FlowSimulation as ReservoirSimulator
from gaia_genesis.prediction import AIPrediction

logger = structlog.get_logger()


def run_flowsim_background_task(
    job_id: uuid.UUID,
    end_time: float,
    dt: float,
    simulator: ReservoirSimulator,
    db_manager: DatabaseManager = None,
):
    session = DatabaseManager.get_instance().get_session()
    try:
        job = session.query(Job).filter(Job.id == job_id).first()
        if not job:
            return

        job.status = "running"
        job.updated_at = datetime.datetime.now(datetime.timezone.utc)
        session.commit()

        simulator.run_simulation(end_time, dt)

        sim_status = simulator.simulation_results.get("status", "Unknown")
        if sim_status == "Failed: Singular matrix":
            raise RuntimeError("Simulation failed due to singular matrix.")

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
            "pressure_at_block": {"0": block0_pressures},
            "status": sim_status,
        }

        job.status = "completed"
        job.result = result_payload
        job.updated_at = datetime.datetime.now(datetime.timezone.utc)
        session.commit()
    except Exception as exc:
        session.rollback()
        job = session.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = "failed"
            job.error = str(exc)
            job.updated_at = datetime.datetime.now(datetime.timezone.utc)
            session.commit()
    finally:
        session.close()


def train_ai_background_task(
    job_id: uuid.UUID,
    records: list,
    target_column: str,
    feature_columns: list,
    predictor: AIPrediction,
    db_manager: DatabaseManager = None,
):
    session = DatabaseManager.get_instance().get_session()
    try:
        job = session.query(Job).filter(Job.id == job_id).first()
        if not job:
            return

        job.status = "running"
        job.updated_at = datetime.datetime.now(datetime.timezone.utc)
        session.commit()

        df = pd.DataFrame(records)
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

        job.status = "completed"
        job.result = result_payload
        job.updated_at = datetime.datetime.now(datetime.timezone.utc)
        session.commit()
    except Exception as exc:
        session.rollback()
        job = session.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = "failed"
            job.error = str(exc)
            job.updated_at = datetime.datetime.now(datetime.timezone.utc)
            session.commit()
    finally:
        session.close()
