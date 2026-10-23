from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uuid

from auth_utils import get_current_active_user, UserResponse
from gaia_genesis.core.database_manager import DatabaseManager
from gaia_genesis.models import Job

router = APIRouter(tags=["Jobs"])


class JobResponse(BaseModel):
    id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@router.get("/{job_id}", response_model=JobResponse)
async def get_job_status(
    job_id: str, current_user: UserResponse = Depends(get_current_active_user)
):
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job_id format"
        )

    session = DatabaseManager.get_instance().get_session()
    try:
        job = session.query(Job).filter(Job.id == job_uuid).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
            )

        if str(job.user_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: You can only view your own jobs",
            )

        return JobResponse(
            id=str(job.id),
            status=job.status,
            result=job.result,
            error=job.error,
            created_at=job.created_at.isoformat() if job.created_at else None,
            updated_at=job.updated_at.isoformat() if job.updated_at else None,
        )
    finally:
        session.close()
