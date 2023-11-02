from app.database import Base
from sqlalchemy import (Column, Integer, Boolean, String, 
            ForeignKey, UniqueConstraint, Date, 
            CheckConstraint, TIMESTAMP, text)

from typing import Literal
from fastapi import HTTPException, status




class User(Base):
    __tablename__ = "User"
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    first_name = Column(String, default=None)
    last_name = Column(String, default=None)
    email = Column(String,unique=True, index = True)
    password = Column(String,nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    # created_at = Column(TIMESTAMP(timezone=True), nullable=False,server_default = text('now()'))
    key = Column(String, default = None)
    key_flag = Column(Boolean, default = False)

# class ResetKey(Base):
#     __tablename__ = "Reset_Key"
    
#     key = Column(String,primary_key=True, nullable=False)