from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=schemas.TaskOut)
def create_task(task: schemas.TaskCreate, db: DBSession = Depends(get_db)):
    db_task = models.Task(
        title=task.title,
        points=task.points,
        due_date=task.due_date or date.today(),
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@router.get("/today", response_model=List[schemas.TaskOut])
def today_tasks(db: DBSession = Depends(get_db)):
    """Today's pending tasks plus anything still marked late from
    before — late items keep showing until done or deleted."""
    today = date.today()
    return (
        db.query(models.Task)
        .filter(
            (models.Task.due_date == today) | (models.Task.status == "late")
        )
        .order_by(models.Task.status.desc(), models.Task.created_at)
        .all()
    )


@router.patch("/{task_id}", response_model=schemas.TaskOut)
def update_task(task_id: int, update: schemas.TaskUpdate, db: DBSession = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    data = update.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}")
def delete_task(task_id: int, db: DBSession = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"ok": True}


@router.post("/rollover-late")
def rollover_late_tasks(db: DBSession = Depends(get_db)):
    """Meant to run once a day (cron / scheduled job), not from the
    UI. Any task still pending from a previous day becomes 'late'
    instead of just vanishing — see spec doc section 5c."""
    today = date.today()
    stale = (
        db.query(models.Task)
        .filter(models.Task.status == "pending", models.Task.due_date < today)
        .all()
    )
    for task in stale:
        task.status = "late"
    db.commit()
    return {"rolled_over": len(stale)}