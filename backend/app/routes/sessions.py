from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _get_session_or_404(session_id: int, db: DBSession) -> models.Session:
    s = db.query(models.Session).filter(models.Session.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    return s


@router.post("/start", response_model=schemas.SessionOut)
def start_session(payload: schemas.SessionStart, db: DBSession = Depends(get_db)):
    now = datetime.utcnow()
    s = models.Session(
        metric_id=payload.metric_id,
        started_at=now,
        last_resumed_at=now,
        accumulated_seconds=0,
        status="running",
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.post("/{session_id}/pause", response_model=schemas.SessionOut)
def pause_session(session_id: int, db: DBSession = Depends(get_db)):
    s = _get_session_or_404(session_id, db)
    if s.status != "running":
        raise HTTPException(status_code=400, detail=f"Session is {s.status}, not running")

    now = datetime.utcnow()
    elapsed = (now - s.last_resumed_at).total_seconds()
    s.accumulated_seconds += int(elapsed)
    s.last_resumed_at = None
    s.status = "paused"
    db.commit()
    db.refresh(s)
    return s


@router.post("/{session_id}/resume", response_model=schemas.SessionOut)
def resume_session(session_id: int, db: DBSession = Depends(get_db)):
    s = _get_session_or_404(session_id, db)
    if s.status != "paused":
        raise HTTPException(status_code=400, detail=f"Session is {s.status}, not paused")

    s.last_resumed_at = datetime.utcnow()
    s.status = "running"
    db.commit()
    db.refresh(s)
    return s


@router.post("/{session_id}/stop", response_model=schemas.SessionOut)
def stop_session(session_id: int, db: DBSession = Depends(get_db)):
    s = _get_session_or_404(session_id, db)
    if s.status == "completed":
        raise HTTPException(status_code=400, detail="Session already completed")

    now = datetime.utcnow()
    if s.status == "running":
        elapsed = (now - s.last_resumed_at).total_seconds()
        s.accumulated_seconds += int(elapsed)

    s.ended_at = now
    s.active_duration_seconds = s.accumulated_seconds
    s.status = "completed"
    db.add(s)

    # Auto-create the matching log entry — this is the only place
    # a 'duration' metric ever gets a log, per the spec doc.
    log = models.Log(
        metric_id=s.metric_id,
        duration_seconds=s.active_duration_seconds,
        logged_at=s.started_at,
        session_id=s.id,
    )
    db.add(log)
    db.commit()
    db.refresh(s)
    return s