from pydantic import BaseModel, Field, validator
from typing import Literal, List, Union
from fastapi import HTTPException, status, UploadFile, File
from fastapi.encoders import jsonable_encoder


import requests


def get_states(states_dict = {}):
		
	url = "https://nigeria-states-towns-lga.onrender.com/api/all"

	response = requests.get(url)
	raw_data = response.json()

	for state in raw_data:
		towns_list = []
		towns = state["towns"]
		for town in towns:
			towns_list.append(town["name"])
		states_dict[state["state_code"]] = towns_list

	state_list = list(states_dict.keys())
	state_list.sort()
	return {"state_lists": state_list, "states_dict": states_dict}


def get_cities(state_code):
	state = get_states()
	return state["states_dict"][state_code]


STATES_DATA_TYPE = Literal['ABIA', 'ADAMAWA', 'AKWA', 'ANAMBRA', 'BAUCHI', 'BAYELSA', 'BENUE', 'BORNO', 'CROSSRIVER', 'DELTA', 'EBONYI',
							 'EDO', 'EKITI', 'ENUGU', 'FCT', 'GOMBE', 'IMO', 'JIGAWA', 
							 'KADUNA', 'KANO', 'KATSINA', 'KEBBI', 'KOGI', 'KWARA', 'LAGOS', 
							 'NASARAWA', 'NIGER', 'OGUN', 'ONDO', 'OSUN', 'OYO', 'PLATEAU', 'RIVERS',
							   'SOKOTO', 'TARABA', 'YOBE', 'ZAMFARA']

ACC_TYPE = Literal['HOTEL', 'GUEST HOUSE', 'LODGE', 'SERVICED APARTMENT', 
				   'HOSTEL', 'RESORT', 'MOTEL',
					'SELF-CON', 'SINGLE ROOM', 'FLAT',  'OTHERS']



class AccomodationProviderSchema(BaseModel):
	brand_name: str = Field(default=None)
	phone_num: str = Field(default=None)
	brand_address: str = Field(default=None)
	state: STATES_DATA_TYPE = Field(default=None)
	city: str = Field(default=None)

	class Config:
		schema_extra = {
			"example": {
				"brand_name": "any",
				"phone_num": "any",
				"brand_address": "any",
				"state": "OSUN",
				"city": "Osogbo"
			}
		}# Custom validator to check if the 'phone_number' is a valid phone number
	@validator("phone_num", pre=True, always=True)
	def check_phone_number(cls, value, values):
		if ( 
			(value[:4] == "+234" and len(value) == 14 and value[1:].isnumeric()) 
	  		or (value[:2] in ['09', '08', '07'] and len(value) == 11 and value.isnumeric()) 
			):
			return value

		else:
			raise HTTPException(
							status_code=status.HTTP_400_BAD_REQUEST,
							detail={
								"status": "error",
								"message": "error validating phone number,invalid phone number",
								"body": {
									"phone_number": value
								}
							}
							)		
	# Custom validator to set the type of 'city' based on the value of 'state'
	@validator("city", pre=True, always=True)
	def set_city_type(cls, value, values):
		state_value = values.get("state")
		if state_value:
			state_cities = get_cities(state_value)
			if value in state_cities:
				return value
			else:
				raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail={
                                "status": "error",
                                "message": "City not found in state",
                                "body": {
                                    "state": state_value,
									"city": value
								}
                            }
                            )
		else:
			raise HTTPException(
							status_code=status.HTTP_400_BAD_REQUEST,
							detail={
								"status": "error",
								"message": "State not found",
								"body": {
									"state": state_value,
									"city": value
								}
							}
							)

	

class OurBaseModel(BaseModel):
    class Config:
        orm_mode = True

class AccomodationProviderListingSchema(OurBaseModel):
	accomodation_name: str = Field(default=None)
	description: str = Field(default=None)
	accomodation_address: str = Field(default=None)
	accomodation_type: ACC_TYPE = Field(default=None)
	number_of_rooms: int = Field(default=None)
	number_of_kitchen: int = Field(default=None)
	number_of_bathrooms: int = Field(default=None)
	state: STATES_DATA_TYPE = Field(default=None)
	city: str = Field(default=None)
	
	class Config:
		schema_extra = {
			"example": {
				"accomodation_name": "any",
				"description": "any",
				"accomodation_address": "any",
				"accomodation_type": "any",
				"number_of_rooms": 0,
				"number_of_kitchen": 0,
				"number_of_bathrooms": 0,
				"state": "any",
				"city": "any"
			}
		}
	
	# Custom validator to set the type of 'city' based on the value of 'state'
	@validator("city", pre=True, always=True)
	def set_city_type(cls, value, values):
		state_value = values.get("state")
		if state_value:
			state_cities = get_cities(state_value)
			if value in state_cities:
				return value
			else:
				raise HTTPException(
							status_code=status.HTTP_400_BAD_REQUEST,
							detail={
								"status": "error",
								"message": "City not found in state",
								"body": {
									"state": state_value,
									"city": value
								}
							}
							)
		else:
			raise HTTPException(
							status_code=status.HTTP_400_BAD_REQUEST,
							detail={
								"status": "error",
								"message": "State not found",
								"body": {
									"state": state_value,
									"city": value
								}
							}
							)
	#set the custom validator to only allow at least three accomodation images
	# @validator("accom_images", pre=True, always=True)
	# def set_accomodation_images_type(cls, value, values):
	# 	accomodation_images = values.get("accom_images")
	# 	if len(accomodation_images) < 3:
	# 		raise HTTPException(
	# 						status_code=status.HTTP_400_BAD_REQUEST,
	# 						detail={
	# 							"status": "error",
	# 							"message": "At least three accomodation images are required",
	# 							"body": {
	# 								"accomodation_images": accomodation_images
	# 							}
	# 						}
	# 						)
	# 	else:
	# 		return value
	

		


	
    