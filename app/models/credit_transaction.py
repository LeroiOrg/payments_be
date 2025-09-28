from sqlalchemy import Column, Integer, String, TIMESTAMP, func
from app.db.session import Base

class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False)
    credits = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    status = Column(String(50), nullable=False)  # approved, pending, failed
    payment_id = Column(String(255), nullable=False)
    session_id = Column(String, nullable=False) 
    token = Column(String(512), nullable=False)
