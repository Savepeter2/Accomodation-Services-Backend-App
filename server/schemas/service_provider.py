from pydantic import BaseModel, Field, validator
from typing import Literal, List, Union
from fastapi import HTTPException, status
from schemas.acc_prov import get_states, get_cities
import requests


STATES_DATA_TYPE = Literal['ABIA', 'ADAMAWA', 'AKWA', 'ANAMBRA', 'BAUCHI', 'BAYELSA', 'BENUE', 'BORNO', 'CROSSRIVER', 'DELTA', 'EBONYI',
							 'EDO', 'EKITI', 'ENUGU', 'FCT', 'GOMBE', 'IMO', 'JIGAWA', 
							 'KADUNA', 'KANO', 'KATSINA', 'KEBBI', 'KOGI', 'KWARA', 'LAGOS', 
							 'NASARAWA', 'NIGER', 'OGUN', 'ONDO', 'OSUN', 'OYO', 'PLATEAU', 'RIVERS',
							   'SOKOTO', 'TARABA', 'YOBE', 'ZAMFARA']

class OurBaseModel(BaseModel):
    class Config:
        orm_mode = True
    
class ServiceProviderSchema(BaseModel):
    brand_name: str = Field(default=None)
    Area_Of_Specialization: str = Field(default=None)
    phone_number: str = Field(default=None)
    brand_address: str = Field(default=None)
    state: STATES_DATA_TYPE = Field(default=None)
    city: str = Field(default=None)

    class Config:
        schema_extra = {
            "example": {
                "brand_name": "any",
                "phone_number": "any",
                "brand_address": "any",
                "Area_Of_Specialization": "any",
                "state": "any",
                "city": "any"
            }
        }

    # Custom validator to set the type of 'city' based on the value of 'state'
    @validator("city", pre=True, always=True)
    def set_city_type(cls, value, values):
        state_value = values.get("state")
        cities = get_cities(state_value)
        if value not in cities:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Invalid city",
                    "body": "Invalid city"
                }
            )
        return value
    
    #custom validator to check if the phone number is valid
    @validator("phone_number", pre=True, always=True)
    def set_phone_number_type(cls, value, values):
        phone_number = values.get("phone_number")
        if phone_number:
            if len(phone_number) != 11:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "status": "error",
                        "message": "Invalid phone number",
                        "body": {
                            "phone_number": phone_number
                        }
                    }
                )
            
            if phone_number[:2] not in ['09', '08', '07']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "status": "error",
                        "message": "Invalid phone number",
                        "body": {
                            "phone_number": phone_number
                        }
                    }
                )
            return value
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Invalid phone number",
                    "body": "Invalid phone number"
                }
            )
    
            

        


class ServiceProviderOutSchema(OurBaseModel):
    status: str = Field(default=None)
    message: str = Field(default=None)
    body: ServiceProviderSchema = Field(default=None)


