from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True, index=True)
    markup_percentage = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    workspace = relationship("Workspace", back_populates="suppliers")
    invoices = relationship("Invoice", back_populates="supplier", cascade="all, delete-orphan")

    # Composite index for workspace + email lookups
    __table_args__ = (
        Index('idx_supplier_workspace_email', 'workspace_id', 'email'),
    )
