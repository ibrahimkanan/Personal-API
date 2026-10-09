from collections import defaultdict
from datetime import timedelta
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session as DBSession

from .. import models, schemas
from ..database import get_db
from ..timeutils import APP_TZ_NAME, day_bounds, local_today

router = APIRouter(prefix="/metrics", tags=["metrics"])

PERIOD_DAYS = {"week": 7, "month": 30, "year": 365}


def _local_day_col():
    # Group logs by the day in YOUR timezone, not the database's.
    return func.date(func.timezone(APP_TZ_NAME, models.Log.logged_at))


def _since(period: str):
    days = PERIOD_DAYS.get(period, 7)
    return day_bounds(local_today() - timedelta(days=days - 1))[0]


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
    """Everything the Today screen needs in one call. Status is driven purely
    by whether a log exists inside today's local-day window — nothing is ever
    'reset', tomorrow's window is simply empty."""
    start, end = day_bounds(local_today())

    metrics = db.query(models.Metric).order_by(models.Metric.group_name, models.Metric.id).all()

    logs_by_metric = defaultdict(list)
    for log in (
        db.query(models.Log)
        .filter(models.Log.logged_at >= start, models.Log.logged_at < end)
        .order_by(models.Log.logged_at)
        .all()
    ):
        logs_by_metric[log.metric_id].append(log)

    active_by_metric = {
        s.metric_id: s
        for s in db.query(models.Session)
        .filter(models.Session.status.in_(["running", "paused"]))
        .order_by(models.Session.id)
        .all()
    }

    result = []
    for m in metrics:
        logs = logs_by_metric.get(m.id, [])
        last = logs[-1] if logs else None
        durations = [l.duration_seconds for l in logs if l.duration_seconds is not None]
        s = active_by_metric.get(m.id)
        result.append(
            {
                "metric_id": m.id,
                "name": m.name,
                "type": m.type,
                "unit": m.unit,
                "group_name": m.group_name,
                "done": bool(logs),
                "log_id": last.id if last else None,
                "value": float(last.value) if last and last.value is not None else None,
                "duration_seconds": sum(durations) if durations else None,
                "session": (
                    {
                        "id": s.id,
                        "status": s.status,
                        "accumulated_seconds": s.accumulated_seconds,
                        "last_resumed_at": s.last_resumed_at.isoformat() if s.last_resumed_at else None,
                    }
                    if s
                    else None
                ),
            }
        )
    return result


@router.get("/{metric_id}/summary")
def metric_summary(metric_id: int, period: str = "week", db: DBSession = Depends(get_db)):
    day = _local_day_col()
    rows = (
        db.query(
            day.label("day"),
            func.sum(models.Log.duration_seconds).label("total_duration"),
            func.sum(models.Log.value).label("total_value"),
            func.count(models.Log.id).label("count"),
        )
        .filter(models.Log.metric_id == metric_id, models.Log.logged_at >= _since(period))
        .group_by(day)
        .order_by(day)
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
    day = _local_day_col()
    rows = (
        db.query(day.label("day"), func.count(models.Log.id).label("done_count"))
        .join(models.Metric, models.Metric.id == models.Log.metric_id)
        .filter(models.Metric.group_name == group_name, models.Log.logged_at >= _since(period))
        .group_by(day)
        .order_by(day)
        .all()
    )
    total_in_group = (
        db.query(models.Metric).filter(models.Metric.group_name == group_name).count()
    )
    return {
        "group_name": group_name,
        "total_in_group": total_in_group,
        "days": [{"day": str(r.day), "done_count": r.done_count} for r in rows],
    }