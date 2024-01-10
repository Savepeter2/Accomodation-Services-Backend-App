from app.database import Base
from sqlalchemy import (Column, Integer, Boolean, String, 
                        
            ForeignKey, UniqueConstraint, Date, 
            CheckConstraint, TIMESTAMP, text,
            DateTime, func)

from typing import Literal
from fastapi import HTTPException, status
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy import PickleType
from sqlalchemy.orm import relationship


SQLALchList = MutableList.as_mutable(PickleType)

class User(Base):
    __tablename__ = "User"
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    first_name = Column(String, default=None)
    last_name = Column(String, default=None)
    email = Column(String,unique=True, index = True)
    password = Column(String,nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    principal = Column(String, default="user")
    profile = Column(String, default = None)
    key = Column(String, default = None)
    key_flag = Column(Boolean, default = False)
    profile_picture_url = Column(String, default = None)


class AccomodationProvider(Base):
    __tablename__ = "Accomodation_Provider"
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    brand_name = Column(String, default=None)
    phone_number = Column(String, default=None, unique=True)
    brand_address = Column(String, default=None)
    city = Column(String, default=None)
    state = Column(String, default=None)
    user_id = Column(Integer, ForeignKey("User.id"))
    profile_picture_url = Column(String, default=None)
    # acc_prov_picture = Column(String, default=None)
    # acc_prov_thumbnail_picture = Column(String, default = None)
    profile_visits = Column(Integer, default = 0)
    created_at = Column(DateTime(timezone=True))

    # user = relationship("User", back_populates="accomodation_provider")
  
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
    # images_thumbnail = Column(SQLALchList, default=[])
    number_of_rooms = Column(Integer, default=None)
    number_of_kitchens = Column(Integer, default=None)
    number_of_bathrooms = Column(Integer, default=None)
    reviews = Column(SQLALchList, default = [])
    no_likes = Column(Integer, default = 0)


class UserListingLikes(Base):
    __tablename__ = "User_Listing_Likes"
    id = Column(Integer, primary_key=True, autoincrement=True, index = True)
    user_id = Column(Integer, ForeignKey("User.id"))
    listing_id = Column(Integer, ForeignKey("Accomodation_Provider_Listing.id"))
    liked = Column(Boolean, default = False)

class AccomodationProviderProfileVisitStats(Base):
    __tablename__ = "Accomodation_Provider_Profile_Visit_Stats"
    id = Column(Integer, primary_key=True, autoincrement=True, index = True)
    acc_provider_id = Column(Integer, ForeignKey("Accomodation_Provider.id"))
    user_explorer_id = Column(Integer, ForeignKey("User.id"))
    visit_date = Column(DateTime(timezone=True))
    profile_visit = Column(Integer, default = 0)

