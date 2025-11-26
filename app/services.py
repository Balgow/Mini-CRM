from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional, List
import random
from app import models, schemas


class LeadService:
    """Service for managing leads"""
    
    @staticmethod
    def find_or_create_lead(
        db: Session,
        external_id: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        name: Optional[str] = None
    ) -> models.Lead:
        """
        Find existing lead by external_id, phone, or email.
        If not found, create a new lead.
        """
        # Try to find by external_id first
        if external_id:
            lead = db.query(models.Lead).filter(models.Lead.external_id == external_id).first()
            if lead:
                return lead
        
        # Try to find by phone
        if phone:
            lead = db.query(models.Lead).filter(models.Lead.phone == phone).first()
            if lead:
                return lead
        
        # Try to find by email
        if email:
            lead = db.query(models.Lead).filter(models.Lead.email == email).first()
            if lead:
                return lead
        
        # Create new lead
        lead = models.Lead(
            external_id=external_id,
            phone=phone,
            email=email,
            name=name
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)
        return lead


class DistributionService:
    """Service for distributing contacts to operators"""
    
    @staticmethod
    def get_available_operators(
        db: Session,
        source_id: int
    ) -> List[models.Operator]:
        """
        Get all available operators for a source:
        - Operator is active
        - Operator has weight configured for this source
        - Operator hasn't exceeded load limit
        """
        # Get all operators with weights for this source
        source_weights = db.query(models.SourceOperatorWeight).filter(
            models.SourceOperatorWeight.source_id == source_id
        ).all()
        
        if not source_weights:
            return []
        
        available_operators = []
        
        for source_weight in source_weights:
            operator = source_weight.operator
            
            # Check if operator is active
            if not operator.is_active:
                continue
            
            # Calculate current load (count of active contacts)
            current_load = db.query(func.count(models.Contact.id)).filter(
                and_(
                    models.Contact.operator_id == operator.id,
                    models.Contact.is_active == True
                )
            ).scalar()
            
            # Check if load limit is not exceeded
            if current_load < operator.load_limit:
                available_operators.append(operator)
        
        return available_operators
    
    @staticmethod
    def select_operator_by_weight(
        db: Session,
        source_id: int,
        available_operators: List[models.Operator]
    ) -> Optional[models.Operator]:
        """
        Select an operator using weighted random distribution.
        Uses probability = weight / sum_of_weights
        """
        if not available_operators:
            return None
        
        # Get weights for available operators
        operator_weights = []
        for operator in available_operators:
            weight = db.query(models.SourceOperatorWeight).filter(
                and_(
                    models.SourceOperatorWeight.source_id == source_id,
                    models.SourceOperatorWeight.operator_id == operator.id
                )
            ).first()
            
            if weight:
                operator_weights.append((operator, weight.weight))
        
        if not operator_weights:
            return None
        
        # Calculate total weight
        total_weight = sum(weight for _, weight in operator_weights)
        
        if total_weight == 0:
            # If all weights are 0, return random operator
            return random.choice(available_operators)
        
        # Weighted random selection
        rand = random.uniform(0, total_weight)
        cumulative = 0
        
        for operator, weight in operator_weights:
            cumulative += weight
            if rand <= cumulative:
                # Double-check load limit (in case of race condition)
                current_load = db.query(func.count(models.Contact.id)).filter(
                    and_(
                        models.Contact.operator_id == operator.id,
                        models.Contact.is_active == True
                    )
                ).scalar()
                
                if current_load < operator.load_limit:
                    return operator
        
        # Fallback to first available (shouldn't happen, but just in case)
        return available_operators[0]
    
    @staticmethod
    def assign_operator(
        db: Session,
        source_id: int
    ) -> Optional[models.Operator]:
        """
        Main method to assign an operator for a contact from a source.
        Returns None if no suitable operator is available.
        """
        available_operators = DistributionService.get_available_operators(db, source_id)
        
        if not available_operators:
            return None
        
        return DistributionService.select_operator_by_weight(db, source_id, available_operators)


class ContactService:
    """Service for managing contacts"""
    
    @staticmethod
    def create_contact(
        db: Session,
        contact_data: schemas.ContactCreate
    ) -> models.Contact:
        """
        Create a new contact:
        1. Find or create lead
        2. Determine source
        3. Assign operator
        4. Create contact record
        """
        # 1. Find or create lead
        lead = LeadService.find_or_create_lead(
            db=db,
            external_id=contact_data.lead_external_id,
            phone=contact_data.lead_phone,
            email=contact_data.lead_email,
            name=contact_data.lead_name
        )
        
        # 2. Verify source exists
        source = db.query(models.Source).filter(models.Source.id == contact_data.source_id).first()
        if not source:
            raise ValueError(f"Source with id {contact_data.source_id} not found")
        
        # 3. Assign operator
        operator = DistributionService.assign_operator(db, contact_data.source_id)
        
        # 4. Create contact
        contact = models.Contact(
            lead_id=lead.id,
            source_id=contact_data.source_id,
            operator_id=operator.id if operator else None,
            message=contact_data.message,
            is_active=True
        )
        db.add(contact)
        db.commit()
        db.refresh(contact)
        return contact

