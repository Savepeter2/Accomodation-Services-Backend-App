from app.database import Base
from sqlalchemy import (Column, Integer, Boolean, String, 
                        
            ForeignKey, UniqueConstraint, Date, 
            CheckConstraint, TIMESTAMP, text)

from typing import Literal
from fastapi import HTTPException, status
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy import PickleType


SQLALchList = MutableList.as_mutable(PickleType)

class User(Base):
    __tablename__ = "User"
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    first_name = Column(String, default=None)
    last_name = Column(String, default=None)
    email = Column(String,unique=True, index = True)
    password = Column(String,nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    profile = Column(String, default = None)
    # created_at = Column(TIMESTAMP(timezone=True), nullable=False,server_default = text('now()'))
    key = Column(String, default = None)
    key_flag = Column(Boolean, default = False)


# class ResetKey(Base):
#     __tablename__ = "Reset_Key"
    
#     key = Column(String,primary_key=True, nullable=False)

class AccomodationProvider(Base):
    __tablename__ = "Accomodation_Provider"
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    brand_name = Column(String, default=None)
    phone_number = Column(String, default=None, unique=True)
    brand_address = Column(String, default=None)
    city = Column(String, default=None)
    state = Column(String, default=None)
    user_id = Column(Integer, ForeignKey("User.id"))
  
class ServiceProvider(Base):
    __tablename__ = "Service_Provider"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    brand_name = Column(String, default=None)
    Area_Of_Specialization = Column(String, default=None)
    phone_number = Column(String, default=None, unique=True)
    brand_address = Column(String, default=None)
    city = Column(String, default=None)
    state = Column(String, default=None)
    user_id = Column(Integer, ForeignKey("User.id"))

class AccomodationProviderListing(Base):
    __tablename__ = "Accomodation_Provider_Listing"
    id = Column(Integer, primary_key=True, autoincrement=True, index = True)
    acc_provider_id = Column(Integer, ForeignKey("Accomodation_Provider.id"))
    accomodation_type = Column(String, default=None)
    accomodation_name = Column(String, default=None)
    accomodation_address = Column(String, default=None)
    accomodation_city = Column(String, default=None)
    accomodation_state = Column(String, default=None)
    accomodation_description = Column(String, default=None)
    accom_images = Column(SQLALchList, default=[])
    images_thumbnail = Column(SQLALchList, default=[])
    number_of_rooms = Column(Integer, default=None)
    number_of_kitchens = Column(Integer, default=None)
    number_of_bathrooms = Column(Integer, default=None)



    
