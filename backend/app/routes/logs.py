from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DBSession

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/logs", tags=["logs"])


@router.post("", response_model=schemas.LogOut)
def create_log(log: schemas.LogCreate, db: DBSession = Depends(get_db)):
    db_log = models.Log(
        metric_id=log.metric_id,
        value=log.value,
        duration_seconds=log.duration_seconds,
        logged_at=log.logged_at or datetime.utcnow(),
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log