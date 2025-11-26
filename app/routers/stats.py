from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Dict
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/stats", tags=["statistics"])


@router.get("/distribution")
def get_distribution_stats(db: Session = Depends(get_db)):
    """
    Get distribution statistics showing how contacts are distributed
    across operators and sources
    """
    sources = db.query(models.Source).all()
    
    result = []
    for source in sources:
        # Count total contacts for this source
        total_contacts = db.query(func.count(models.Contact.id)).filter(
            models.Contact.source_id == source.id
        ).scalar()
        
        # Count contacts by operator
        contacts_by_operator = {}
        operator_contacts = db.query(
            models.Contact.operator_id,
            func.count(models.Contact.id).label('count')
        ).filter(
            models.Contact.source_id == source.id
        ).group_by(models.Contact.operator_id).all()
        
        for operator_id, count in operator_contacts:
            if operator_id:
                operator = db.query(models.Operator).filter(models.Operator.id == operator_id).first()
                if operator:
                    contacts_by_operator[operator_id] = {
                        "operator_name": operator.name,
                        "count": count
                    }
        
        result.append({
            "source_id": source.id,
            "source_name": source.name,
            "total_contacts": total_contacts,
            "contacts_by_operator": contacts_by_operator
        })
    
    return result


@router.get("/leads-summary")
def get_leads_summary(db: Session = Depends(get_db)):
    """
    Get summary of leads showing that one lead can have multiple contacts
    from different sources
    """
    leads = db.query(models.Lead).all()
    
    result = []
    for lead in leads:
        contacts_info = []
        for contact in lead.contacts:
            contacts_info.append({
                "contact_id": contact.id,
                "source_id": contact.source_id,
                "source_name": contact.source.name if contact.source else None,
                "operator_id": contact.operator_id,
                "operator_name": contact.operator.name if contact.operator else None,
                "created_at": contact.created_at.isoformat()
            })
        
        result.append({
            "lead_id": lead.id,
            "lead_external_id": lead.external_id,
            "lead_phone": lead.phone,
            "lead_email": lead.email,
            "lead_name": lead.name,
            "total_contacts": len(lead.contacts),
            "contacts": contacts_info
        })
    
    return result

