from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class DocumentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    REJECTED = "rejected"


class PendingDocument(Base):
    __tablename__ = "pending_documents"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    pdf_url = Column(String(500), nullable=False)
    filename = Column(String(255), nullable=False)
    status = Column(ENUM('pending', 'processed', 'rejected', name='documentstatus'), nullable=False, default="pending", index=True)
    gmail_message_id = Column(String(255), nullable=True, index=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    workspace = relationship("Workspace", back_populates="pending_documents")
