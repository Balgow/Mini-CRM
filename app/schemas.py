from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# Operator schemas
class OperatorBase(BaseModel):
    name: str
    is_active: bool = True
    load_limit: int = 10


class OperatorCreate(OperatorBase):
    pass


class OperatorUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    load_limit: Optional[int] = None


class OperatorResponse(OperatorBase):
    id: int
    
    class Config:
        from_attributes = True


# Source schemas
class SourceBase(BaseModel):
    name: str
    description: Optional[str] = None


class SourceCreate(SourceBase):
    pass


class SourceResponse(SourceBase):
    id: int
    
    class Config:
        from_attributes = True


# Source-Operator Weight schemas
class SourceOperatorWeightBase(BaseModel):
    operator_id: int
    weight: float


class SourceOperatorWeightCreate(SourceOperatorWeightBase):
    pass


class SourceOperatorWeightResponse(SourceOperatorWeightBase):
    id: int
    source_id: int
    operator_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class SourceConfiguration(BaseModel):
    """Configuration for a source with operator weights"""
    source_id: int
    operator_weights: List[SourceOperatorWeightCreate]


# Lead schemas
class LeadBase(BaseModel):
    external_id: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None


class LeadCreate(LeadBase):
    pass


class LeadResponse(LeadBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Contact schemas
class ContactBase(BaseModel):
    message: Optional[str] = None


class ContactCreate(ContactBase):
    """Data for creating a new contact"""
    lead_external_id: Optional[str] = None
    lead_phone: Optional[str] = None
    lead_email: Optional[str] = None
    lead_name: Optional[str] = None
    source_id: int


class ContactResponse(ContactBase):
    id: int
    lead_id: int
    source_id: int
    operator_id: Optional[int] = None
    is_active: bool
    created_at: datetime
    lead: Optional[LeadResponse] = None
    source: Optional[SourceResponse] = None
    operator: Optional[OperatorResponse] = None
    
    class Config:
        from_attributes = True


# Statistics/View schemas
class OperatorLoadInfo(BaseModel):
    """Information about operator's current load"""
    operator_id: int
    operator_name: str
    current_load: int
    load_limit: int
    is_active: bool


class DistributionStats(BaseModel):
    """Statistics about distribution"""
    source_id: int
    source_name: str
    total_contacts: int
    contacts_by_operator: dict[int, int]  # operator_id -> count

