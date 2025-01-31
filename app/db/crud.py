from sqlalchemy.orm import Session
from . import models
from datetime import datetime

def create_project(db: Session, name: str, path: str):
    db_project = models.Project(name=name, path=path)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

def delete_project(db: Session, path: str):
    project = db.query(models.Project).filter(models.Project.path == path).first()
    if project:
        db.delete(project)
        db.commit()
    return project

def get_project(db: Session, path: str):
    return db.query(models.Project).filter(models.Project.path == path).first()

def get_projects(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Project).offset(skip).limit(limit).all()