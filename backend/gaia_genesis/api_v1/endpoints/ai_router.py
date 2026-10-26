from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import pandas as pd
import structlog
from gaia_genesis.prediction.ai_prediction import AIPrediction
from auth_utils import get_current_active_user, UserResponse

logger = structlog.get_logger()
router = APIRouter(tags=["AI Prediction"])
ai_engine = AIPrediction()


class TrainRequest(BaseModel):
    records: List[Dict[str, Any]]
    target: str
    features: List[str]


@router.post("/train")
async def train_ai_model(
    data: TrainRequest, user: UserResponse = Depends(get_current_active_user)
):
    log = logger.bind(user_id=str(user.id))
    log.info("Starting AI model training", num_records=len(data.records))

    try:
        df = pd.DataFrame(data.records)
        X_train, X_test, y_train, y_test = ai_engine.prepare_data(
            df, data.target, data.features
        )
        ai_engine.train_models(X_train, y_train, X_test, y_test)

        best_model_name = ai_engine.best_model
        metrics = ai_engine.models[best_model_name]

        log.info(
            "AI model training complete",
            best_model=best_model_name,
            r2=metrics.get("test_r2"),
        )

        return {
            "message": "Models trained successfully",
            "best_model": best_model_name,
            "metrics": {"r2": metrics.get("test_r2"), "rmse": metrics.get("test_rmse")},
        }
    except Exception as e:
        log.error("AI training failed", error=str(e))
        raise HTTPException(status_code=400, detail=f"Training failed: {str(e)}")


class PredictRequest(BaseModel):
    records: List[Dict[str, Any]]


@router.post("/predict")
async def predict_production(
    data: PredictRequest, user: UserResponse = Depends(get_current_active_user)
):
    log = logger.bind(user_id=str(user.id))
    try:
        df = pd.DataFrame(data.records)
        predictions = ai_engine.predict(df)
        return {"predictions": predictions.tolist()}
    except Exception as e:
        log.error("AI prediction failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
