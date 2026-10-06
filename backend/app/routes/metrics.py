from datetime import date, datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session as DBSession

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.post("", response_model=schemas.MetricOut)
def create_metric(metric: schemas.MetricCreate, db: DBSession = Depends(get_db)):
    db_metric = models.Metric(**metric.model_dump())
    db.add(db_metric)
    db.commit()
    db.refresh(db_metric)
    return db_metric


@router.post("/group", response_model=List[schemas.MetricOut])
def create_metric_group(group: schemas.MetricGroupCreate, db: DBSession = Depends(get_db)):
    """Create several metrics at once under the same group_name
    (e.g. the 5 prayers), as discussed for the 'no timer' add flow."""
    created = []
    for name in group.items:
        m = models.Metric(name=name, type=group.type, group_name=group.group_name)
        db.add(m)
        created.append(m)
    db.commit()
    for m in created:
        db.refresh(m)
    return created


@router.get("", response_model=List[schemas.MetricOut])
def list_metrics(db: DBSession = Depends(get_db)):
    return db.query(models.Metric).order_by(models.Metric.group_name, models.Metric.id).all()


@router.get("/today")
def metrics_today(db: DBSession = Depends(get_db)):
    """Per-metric status for today, driven purely by whether a log
    exists for today's date — no reset job needed, see spec doc."""
    today = date.today()
    result = []
    for m in db.query(models.Metric).all():
        log = (
            db.query(models.Log)
            .filter(models.Log.metric_id == m.id)
            .filter(func.date(models.Log.logged_at) == today)
            .first()
        )
        result.append(
            {
                "metric_id": m.id,
                "name": m.name,
                "group_name": m.group_name,
                "done": log is not None,
                "value": float(log.value) if log and log.value is not None else None,
                "duration_seconds": log.duration_seconds if log else None,
            }
        )
    return result


@router.get("/{metric_id}/summary")
def metric_summary(metric_id: int, period: str = "week", db: DBSession = Depends(get_db)):
    days = {"week": 7, "month": 30, "year": 365}.get(period, 7)
    since = datetime.utcnow() - timedelta(days=days)
    rows = (
        db.query(
            func.date(models.Log.logged_at).label("day"),
            func.sum(models.Log.duration_seconds).label("total_duration"),
            func.sum(models.Log.value).label("total_value"),
            func.count(models.Log.id).label("count"),
        )
        .filter(models.Log.metric_id == metric_id, models.Log.logged_at >= since)
        .group_by(func.date(models.Log.logged_at))
        .order_by("day")
        .all()
    )
    return [
        {
            "day": str(r.day),
            "total_duration": r.total_duration,
            "total_value": float(r.total_value) if r.total_value is not None else None,
            "count": r.count,
        }
        for r in rows
    ]


@router.get("/group/{group_name}/summary")
def group_summary(group_name: str, period: str = "week", db: DBSession = Depends(get_db)):
    """e.g. 'how many of the 5 prayers were logged per day this week'."""
    days = {"week": 7, "month": 30, "year": 365}.get(period, 7)
    since = datetime.utcnow() - timedelta(days=days)
    rows = (
        db.query(
            func.date(models.Log.logged_at).label("day"),
            func.count(models.Log.id).label("done_count"),
        )
        .join(models.Metric, models.Metric.id == models.Log.metric_id)
        .filter(models.Metric.group_name == group_name, models.Log.logged_at >= since)
        .group_by(func.date(models.Log.logged_at))
        .order_by("day")
        .all()
    )
    total_in_group = db.query(models.Metric).filter(models.Metric.group_name == group_name).count()
    return {
        "group_name": group_name,
        "total_in_group": total_in_group,
        "days": [{"day": str(r.day), "done_count": r.done_count} for r in rows],
    }