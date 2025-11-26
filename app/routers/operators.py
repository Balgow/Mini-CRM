from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas
from app.services import DistributionService

router = APIRouter(prefix="/operators", tags=["operators"])


@router.post("/", response_model=schemas.OperatorResponse)
def create_operator(operator: schemas.OperatorCreate, db: Session = Depends(get_db)):
    """Create a new operator"""
    db_operator = models.Operator(**operator.dict())
    db.add(db_operator)
    db.commit()
    db.refresh(db_operator)
    return db_operator


@router.get("/", response_model=List[schemas.OperatorResponse])
def list_operators(db: Session = Depends(get_db)):
    """Get list of all operators"""
    return db.query(models.Operator).all()


@router.get("/{operator_id}", response_model=schemas.OperatorResponse)
def get_operator(operator_id: int, db: Session = Depends(get_db)):
    """Get operator by ID"""
    operator = db.query(models.Operator).filter(models.Operator.id == operator_id).first()
    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found")
    return operator


@router.patch("/{operator_id}", response_model=schemas.OperatorResponse)
def update_operator(
    operator_id: int,
    operator_update: schemas.OperatorUpdate,
    db: Session = Depends(get_db)
):
    """Update operator (name, is_active, load_limit)"""
    operator = db.query(models.Operator).filter(models.Operator.id == operator_id).first()
    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found")
    
    update_data = operator_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(operator, field, value)
    
    db.commit()
    db.refresh(operator)
    return operator


@router.get("/{operator_id}/load", response_model=schemas.OperatorLoadInfo)
def get_operator_load(operator_id: int, db: Session = Depends(get_db)):
    """Get operator's current load information"""
    operator = db.query(models.Operator).filter(models.Operator.id == operator_id).first()
    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found")
    
    from sqlalchemy import func, and_
    current_load = db.query(func.count(models.Contact.id)).filter(
        and_(
            models.Contact.operator_id == operator.id,
            models.Contact.is_active == True
        )
    ).scalar()
    
    return schemas.OperatorLoadInfo(
        operator_id=operator.id,
        operator_name=operator.name,
        current_load=current_load,
        load_limit=operator.load_limit,
        is_active=operator.is_active
    )

