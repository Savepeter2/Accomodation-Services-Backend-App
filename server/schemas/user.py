from pydantic import BaseModel, Field, EmailStr
from typing import Literal, List
import requests

PROFILE_DATA_TYPE = Literal["Explorer", "Service Provider", "Accomodation Provider"]

# class OurBaseModel(BaseModel):
#     class Config:
#         orm_mode = True

class UserSchema(BaseModel):
    id: int = Field(default=None)
    first_name: str = Field(default=None)
    last_name: str = Field(default=None)
    email: EmailStr = Field(null=False, unique = True)
    profile: PROFILE_DATA_TYPE = Field(default=None)
    password: str = Field(default=None)
    confirm_password: str = Field(default=None)

    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "first_name": "John",
                "last_name": "Doe",
                "email": "johndoe@xyz.com",
                "profile": ["Explorer","Service Provider", "Accomodation Provider"],
                "password": "password",
                "confirm_password": "password"
            }
            }
        
class UserUpdateSchema(BaseModel):
    old_password: str = Field(default=None)
    new_password: str = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "old_password": "any",
                "new_password": "any"
            }
        }
        
class ProfileUpdateSchema(BaseModel):
    first_name: str = Field(default=None)
    last_name: str = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "any",
                "last_name": "any"
            }
        }

class UserProfileSchema(BaseModel):
    first_name: str = Field(default=None)
    last_name: str = Field(default=None)
    email: EmailStr = Field(null=False, unique = True)
    phone_number: str = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "any",
                "last_name": "any",
                "email": "",
                "phone_number": "any"
            }
        }

class UserDeleteSchema(BaseModel):
    email: str = Field(default=None)
    password: str = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "email": "any@gmail.com",
                "password": "any"
            }
        }

class EmailSchema(BaseModel):
    email: EmailStr = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "email": "johndoe@xyz.com"
            }
        }





    