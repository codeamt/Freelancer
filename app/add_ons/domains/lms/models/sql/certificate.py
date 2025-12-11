"""LMS Certificate Model"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.db.base_class import Base


class Certificate(Base):
    """Certificate model for LMS domain"""
    
    __tablename__ = "certificates"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    certificate_url = Column(String)
    issued_at = Column(DateTime, server_default=func.now())
    verification_code = Column(String, unique=True)
    
    # Relationships
    user = relationship("User")
    course = relationship("Course")
    
    def __repr__(self):
        return f"<Certificate(id={self.id}, user_id={self.user_id}, course_id={self.course_id})>"
