from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Operator(Base):
    """Operator model - represents a customer service operator"""
    __tablename__ = "operators"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    load_limit = Column(Integer, default=10, nullable=False)  # Maximum active contacts
    
    # Relationships
    source_weights = relationship("SourceOperatorWeight", back_populates="operator", cascade="all, delete-orphan")
    contacts = relationship("Contact", back_populates="operator")


class Source(Base):
    """Source/Bot model - represents a channel/bot from which leads contact"""
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)
    description = Column(String, nullable=True)
    
    # Relationships
    operator_weights = relationship("SourceOperatorWeight", back_populates="source", cascade="all, delete-orphan")
    contacts = relationship("Contact", back_populates="source")


class SourceOperatorWeight(Base):
    """Many-to-many relationship between Source and Operator with weight"""
    __tablename__ = "source_operator_weights"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)
    operator_id = Column(Integer, ForeignKey("operators.id"), nullable=False)
    weight = Column(Float, nullable=False, default=1.0)  # Weight for distribution
    
    # Relationships
    source = relationship("Source", back_populates="operator_weights")
    operator = relationship("Operator", back_populates="source_weights")
    
    # Unique constraint: one operator can have only one weight per source
    __table_args__ = (
        UniqueConstraint('source_id', 'operator_id', name='uq_source_operator'),
    )


class Lead(Base):
    """Lead model - represents a customer/client"""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, nullable=True, index=True)  # External identifier (phone, email, etc.)
    phone = Column(String, nullable=True, index=True)
    email = Column(String, nullable=True, index=True)
    name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    contacts = relationship("Contact", back_populates="lead", cascade="all, delete-orphan")


class Contact(Base):
    """Contact/Appeal model - represents a specific contact from a lead through a source"""
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)
    operator_id = Column(Integer, ForeignKey("operators.id"), nullable=True)  # Nullable if no operator available
    message = Column(String, nullable=True)  # Optional message/context
    is_active = Column(Boolean, default=True, nullable=False)  # Active contact (counts toward load)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    lead = relationship("Lead", back_populates="contacts")
    source = relationship("Source", back_populates="contacts")
    operator = relationship("Operator", back_populates="contacts")

