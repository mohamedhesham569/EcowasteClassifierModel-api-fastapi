from sqlalchemy.orm import Session
from app import models, schemas, auth
from .auth import pwd_context
from sqlalchemy import func

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)  
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_waste_result(db: Session, waste_result: schemas.ClassificationResultCreate):
    db_result = models.ClassificationResult(**waste_result.dict())
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    return db_result

def get_user_results(db: Session, user_id: int):
    return db.query(models.ClassificationResult).filter(models.ClassificationResult.user_id == user_id).all()


def get_class_counts(db: Session):
    results = db.query(
        models.ClassificationResult.class_name,
        func.count(models.ClassificationResult.class_name).label("count")
    ).group_by(models.ClassificationResult.class_name).all()
    
    return results

