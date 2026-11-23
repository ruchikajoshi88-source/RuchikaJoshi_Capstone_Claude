from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import Task
from src.schemas import TaskCreate, TaskUpdate


def list_tasks(db: Session) -> list[Task]:
    return list(db.scalars(select(Task).order_by(Task.id)))


def get_task(db: Session, task_id: int) -> Task | None:
    return db.get(Task, task_id)


def create_task(db: Session, data: TaskCreate) -> Task:
    task = Task(**data.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task(db: Session, task: Task, data: TaskUpdate) -> Task:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task: Task) -> None:
    db.delete(task)
    db.commit()
