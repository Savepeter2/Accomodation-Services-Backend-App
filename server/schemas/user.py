from pydantic import BaseModel, Field, EmailStr
from typing import Literal, List
import requests
from app.acl import (
    check_permission, all_acl_permission,
    get_active_principals, check_acl
)

from fastapi_permissions import (
    Allow,
    Authenticated,
    Deny,
    Everyone,
    configure_permissions,
    list_permissions,
)

from fastapi import HTTPException, status

permission_exception = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail={
        "status": "error",
        "message": "Insufficient permissions to perform action",
        "body": None,
    },
    headers={"WWW-Authenticate": "Bearer"},
)


Permission = configure_permissions(get_active_principals, permission_exception)
def HasPermissionTo(permit): return Permission(
    check_acl(permit), UserSchema().__acl__())


PROFILE_DATA_TYPE = Literal["Explorer", "Service Provider", "Accomodation Provider"]

# class OurBaseModel(BaseModel):
#     class Config:
#         orm_mode = True

class UserSchema(BaseModel):
    first_name: str = Field(default=None)
    last_name: str = Field(default=None)
    email: EmailStr = Field(null=False, unique = True, default = None)
    profile: PROFILE_DATA_TYPE = Field(default=None)
    password: str = Field(default=None)
    confirm_password: str = Field(default=None)
    principal: str = Field(default=check_permission("user"))


    class Config:
        schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "johndoe@gmail.com",
                "profile": ["Explorer","Service Provider", "Accomodation Provider"],
                "password": "password",
                "confirm_password": "password"
            }
            }
        
    def __acl__(self):
        """ defines who can do what to the model instance
        the function returns a list containing tuples in the form of
        (Allow or Deny, principal identifier, permission name)
        If a role is not listed (like "role:user") the access will be
        automatically deny. It's like a (Deny, Everyone, All) is automatically
        appended at the end.
        """
        return all_acl_permission

        
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





    