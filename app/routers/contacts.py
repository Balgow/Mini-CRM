from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas
from app.services import ContactService

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.post("/", response_model=schemas.ContactResponse)
def create_contact(contact: schemas.ContactCreate, db: Session = Depends(get_db)):
    """
    Register a new contact/appeal from a lead.
    System will:
    1. Find or create lead based on provided identifiers
    2. Assign operator based on source, weights, and load limits
    3. Create contact record
    
    If no suitable operator is available, contact is created without operator (operator_id = null).
    """
    try:
        db_contact = ContactService.create_contact(db, contact)
        
        # Load relationships for response
        db.refresh(db_contact)
        return db_contact
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[schemas.ContactResponse])
def list_contacts(db: Session = Depends(get_db)):
    """Get list of all contacts"""
    return db.query(models.Contact).all()


@router.get("/{contact_id}", response_model=schemas.ContactResponse)
def get_contact(contact_id: int, db: Session = Depends(get_db)):
    """Get contact by ID"""
    contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.patch("/{contact_id}/deactivate")
def deactivate_contact(contact_id: int, db: Session = Depends(get_db)):
    """Deactivate a contact (reduces operator load)"""
    contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    contact.is_active = False
    db.commit()
    return {"message": "Contact deactivated", "contact_id": contact_id}

