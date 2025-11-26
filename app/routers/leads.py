from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("/", response_model=List[schemas.LeadResponse])
def list_leads(db: Session = Depends(get_db)):
    """Get list of all leads"""
    return db.query(models.Lead).all()


@router.get("/{lead_id}", response_model=schemas.LeadResponse)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    """Get lead by ID with all contacts"""
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.get("/{lead_id}/contacts", response_model=List[schemas.ContactResponse])
def get_lead_contacts(lead_id: int, db: Session = Depends(get_db)):
    """Get all contacts for a specific lead"""
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return lead.contacts

