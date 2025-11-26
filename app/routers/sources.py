from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/sources", tags=["sources"])


@router.post("/", response_model=schemas.SourceResponse)
def create_source(source: schemas.SourceCreate, db: Session = Depends(get_db)):
    """Create a new source/bot"""
    db_source = models.Source(**source.dict())
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    return db_source


@router.get("/", response_model=List[schemas.SourceResponse])
def list_sources(db: Session = Depends(get_db)):
    """Get list of all sources"""
    return db.query(models.Source).all()


@router.get("/{source_id}", response_model=schemas.SourceResponse)
def get_source(source_id: int, db: Session = Depends(get_db)):
    """Get source by ID"""
    source = db.query(models.Source).filter(models.Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


@router.post("/{source_id}/operators", response_model=schemas.SourceOperatorWeightResponse)
def add_operator_to_source(
    source_id: int,
    weight_data: schemas.SourceOperatorWeightCreate,
    db: Session = Depends(get_db)
):
    """Add operator to source with weight, or update existing weight"""
    # Verify source exists
    source = db.query(models.Source).filter(models.Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    # Verify operator exists
    operator = db.query(models.Operator).filter(models.Operator.id == weight_data.operator_id).first()
    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found")
    
    # Check if weight already exists
    existing_weight = db.query(models.SourceOperatorWeight).filter(
        models.SourceOperatorWeight.source_id == source_id,
        models.SourceOperatorWeight.operator_id == weight_data.operator_id
    ).first()
    
    if existing_weight:
        # Update existing weight
        existing_weight.weight = weight_data.weight
        db.commit()
        db.refresh(existing_weight)
        result = schemas.SourceOperatorWeightResponse(
            id=existing_weight.id,
            source_id=existing_weight.source_id,
            operator_id=existing_weight.operator_id,
            weight=existing_weight.weight,
            operator_name=operator.name
        )
        return result
    
    # Create new weight
    db_weight = models.SourceOperatorWeight(
        source_id=source_id,
        operator_id=weight_data.operator_id,
        weight=weight_data.weight
    )
    db.add(db_weight)
    db.commit()
    db.refresh(db_weight)
    
    result = schemas.SourceOperatorWeightResponse(
        id=db_weight.id,
        source_id=db_weight.source_id,
        operator_id=db_weight.operator_id,
        weight=db_weight.weight,
        operator_name=operator.name
    )
    return result


@router.get("/{source_id}/operators", response_model=List[schemas.SourceOperatorWeightResponse])
def get_source_operators(source_id: int, db: Session = Depends(get_db)):
    """Get all operators configured for a source with their weights"""
    source = db.query(models.Source).filter(models.Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    weights = db.query(models.SourceOperatorWeight).filter(
        models.SourceOperatorWeight.source_id == source_id
    ).all()
    
    result = []
    for weight in weights:
        result.append(schemas.SourceOperatorWeightResponse(
            id=weight.id,
            source_id=weight.source_id,
            operator_id=weight.operator_id,
            weight=weight.weight,
            operator_name=weight.operator.name
        ))
    
    return result


@router.delete("/{source_id}/operators/{operator_id}")
def remove_operator_from_source(
    source_id: int,
    operator_id: int,
    db: Session = Depends(get_db)
):
    """Remove operator from source configuration"""
    weight = db.query(models.SourceOperatorWeight).filter(
        models.SourceOperatorWeight.source_id == source_id,
        models.SourceOperatorWeight.operator_id == operator_id
    ).first()
    
    if not weight:
        raise HTTPException(status_code=404, detail="Operator not found in source configuration")
    
    db.delete(weight)
    db.commit()
    return {"message": "Operator removed from source"}

