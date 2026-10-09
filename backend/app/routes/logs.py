from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from .. import models, schemas
from ..database import get_db
from ..timeutils import utcnow

router = APIRouter(prefix="/logs", tags=["logs"])


@router.post("", response_model=schemas.LogOut)
def create_log(log: schemas.LogCreate, db: DBSession = Depends(get_db)):
    if not db.query(models.Metric).filter(models.Metric.id == log.metric_id).first():
        raise HTTPException(status_code=404, detail="Metric not found")

    db_log = models.Log(
        metric_id=log.metric_id,
        value=log.value,
        duration_seconds=log.duration_seconds,
        logged_at=log.logged_at or utcnow(),
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


@router.delete("/{log_id}")
def delete_log(log_id: int, db: DBSession = Depends(get_db)):
    """Undo a mistaken tap (e.g. un-checking a prayer). Logs are otherwise
    append-only; this exists only to correct accidental entries."""
    log = db.query(models.Log).filter(models.Log.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    db.delete(log)
    db.commit()
    return {"ok": True}