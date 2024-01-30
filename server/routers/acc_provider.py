from sqlalchemy.orm import Session
from app.database import engine, get_db
from app.deps import get_current_user
from app.model import (User, AccomodationProvider, AccomodationProviderListing,
                        func, AccomodationProviderProfileVisitStats, UserListingLikes)
from schemas.acc_prov import (AccomodationProviderSchema, get_states,
                               get_cities, AccomodationProviderListingSchema)
from app.utils import logger, upload_files_cloud
from schemas.user import UserSchema
from fastapi import APIRouter, Body, Depends, status, Response, HTTPException, File, UploadFile
from routers.user import HasPermissionTo
from fastapi.responses import FileResponse
from typing import Literal, List, Tuple
import os
from random import randint
import uuid
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse
from fastapi import Form
from schemas.acc_prov import ACC_TYPE, STATES_DATA_TYPE
import aiofiles
from PIL import Image
from io import BytesIO
import base64
import time
import cv2
import re
import numpy as np
from skimage import io, transform
from io import BytesIO
from datetime import datetime
import calendar
import matplotlib.pyplot as plt

router = APIRouter()

async def visualize_profile_visits_chart(chart_data):
    month_labels = chart_data.get('month_labels')
    visits_data = chart_data.get('visits_data')

    plt.plot(month_labels, visits_data,marker='o')
    plt.xlabel("Months")
    plt.ylabel("No. of visits")
    plt.title("Profile visits trend")
    plt.grid(True)

    # Save the chart image to a BytesIO object
    img_buf = BytesIO()
    plt.savefig(img_buf, format='png')
    img_buf.seek(0)

    # Encode the image as base64
    chart_image = base64.b64encode(img_buf.read()).decode('utf-8')
    plt.close()

    return chart_image
            
async def validate_city(city: str, state: str):
    state_cities = get_cities(state)
    if city not in state_cities:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "message": "There is no such city in the state you selected",
                "body": ""
            }
        )
    return city

async def capitalize_city(city:str):
    if not city:
        return city
    return city.capitalize() 
   
async def validate_phone_number(phone_num: str):

    if phone_num is not None:
        if (
            (phone_num[:4] == "+234" and len(phone_num) == 14 and phone_num[1:].isnumeric()) 
            or (phone_num[:2] in ['09', '08', '07'] and len(phone_num) == 11 and phone_num[1:].isnumeric())
            ):
                return phone_num
        
        else:
             raise HTTPException(
                  status_code= status.HTTP_400_BAD_REQUEST,
                  detail = {
                    "status":"error",
                  "message": "Invalid phone number",
                  "body": {
                       "phone_number": phone_num
                  }
             }
             )
    else:
        raise HTTPException(
                  status_code= status.HTTP_400_BAD_REQUEST,
                  detail = {
                    "status":"error",
                  "message": "Error Validating Phone Number, Cannot be empty",
                  "body": {
                       "phone_number": phone_num
                  }
             }
             )



@router.post("/accomodation_provider/create", tags=["Accomodation Provider"])
async def create_accom_provider_profile(
    acc_prov_schema: AccomodationProviderSchema, 
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user),
    permits: list = HasPermissionTo("edit")

):
    try:
        acc_prov = db.query(AccomodationProvider).filter(AccomodationProvider.id == current_user.get('id')).first()
        check_curr_user = db.query(User).filter(User.id == current_user.get('id')).first()
        check_prov = db.query(AccomodationProvider).filter(AccomodationProvider.user_id == current_user.get('id')).first()

        if acc_prov is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Accomodation Provider profile already exists",
                    "body": ""
                }
            )
        
        if check_prov is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Accomodation Provider profile already exists",
                    "body": ""
                }
            )

        if check_curr_user.profile != "Accomodation Provider" and check_curr_user.profile is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "status": "error",
                        "message": "You can't create an Accomodation Provider profile, you are not an Accomodation Provider",
                        "body": ""
                    }
                )
        
        capitalized_city = await capitalize_city(acc_prov_schema.city)
        validated_city = await validate_city(capitalized_city, acc_prov_schema.state)
        validated_phone_num = await validate_phone_number(acc_prov_schema.phone_num)
 
        new_acc_prov = AccomodationProvider(
            brand_name = acc_prov_schema.brand_name,
            phone_number = validated_phone_num,
            brand_address = acc_prov_schema.brand_address,
            state = acc_prov_schema.state,
            city = validated_city,
            user_id = current_user.get('id')
        )

        check_curr_user.profile = "Accomodation Provider"
        db.commit()
        db.refresh(check_curr_user)

        db.add(new_acc_prov)
        db.commit()
        db.refresh(new_acc_prov)

        return {
            "status": "success",
            "message": "Accomodation Provider profile created successfully",
            "body": new_acc_prov
        }
    
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"An error occured while creating Accomodation Provider profile: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "An error occured while creating Accomodation Provider profile",
                    "body": str(e)
                }
            )
        else:
            raise e


@router.get("/accomodation_provider/profile/me", tags=["Accomodation Provider"])
async def get_accom_provider_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    permits: list = HasPermissionTo("view")
):
    try:
        acc_prov = db.query(AccomodationProvider).filter(AccomodationProvider.user_id == current_user.get('id')).first()
        check_curr_user = db.query(User).filter(User.id == current_user.get('id')).first()

        if acc_prov is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Accomodation Provider profile does not exist",
                    "body": ""
                }
            )
        
        return {
            "status": "success",
            "message": "Accomodation Provider profile retrieved successfully",
            "body": acc_prov
        }
    
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"An error occured while retrieving Accomodation Provider profile: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "An error occured while retrieving Accomodation Provider profile",
                    "body": str(e)
                }
            )
        else:
            raise e


@router.patch("/accomodation_provider/profile/me/update", tags=["Accomodation Provider"])
async def update_accom_provider_profile(
    brand_name: str = Form(default=None) ,
	phone_number: str = Form(default=None),
	brand_address: str = Form(default=None),
	state: STATES_DATA_TYPE = Form(default=None) ,
	city: str = Form(default=None),
    profile_picture : UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        acc_to_update = db.query(AccomodationProvider).filter(AccomodationProvider.user_id == current_user.get('id')).first()
        check_curr_user = db.query(User).filter(User.id == current_user.get('id')).first()

        if check_curr_user.profile != "Accomodation Provider" and check_curr_user.profile is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "status": "error",
                        "message": "You can't update an Accomodation Provider profile, you are not an Accomodation Provider",
                        "body": ""
                    }
                )
        
        if acc_to_update is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Accomodation Provider profile not found",
                    "body": ""
                }
            )
        
        capitalized_city = await capitalize_city(city)
        validated_city = await validate_city(capitalized_city, state)
        # image_name, thumbnail_name = await image_upload(profile_picture)
        validated_phone_num = await validate_phone_number(phone_number)
        image_url = upload_files_cloud(profile_picture)

        acc_to_update.brand_name = brand_name
        acc_to_update.phone_number = validated_phone_num
        acc_to_update.brand_address = brand_address
        acc_to_update.state = state
        acc_to_update.city = validated_city
        acc_to_update.profile_picture_url = image_url
        # acc_to_update.acc_prov_picture = image_name
        # acc_to_update.acc_prov_thumbnail_picture = thumbnail_name
        acc_to_update.phone_number = validated_phone_num

        db.commit()
        db.refresh(acc_to_update)

        return {
            "status": "success",
            "message": "Accomodation Provider profile updated successfully",
            "body": acc_to_update
        }
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"An error occured while updating Accomodation Provider profile: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "An error occured while updating Accomodation Provider profile",
                    "body": str(e)
                }
            )
        else:
            raise e
 

@router.get("/accomodation_provider/home", tags=["Accomodation Provider"])
async def accom_provider_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    permits: list = HasPermissionTo("view")
):
    
    try:
        acc_prov = db.query(AccomodationProvider).filter(AccomodationProvider.user_id == current_user.get('id')).first()
        if acc_prov is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Accomodation Provider profile does not exist",
                    "body": ""
                }
            )
        
        listings = db.query(AccomodationProviderListing).filter(AccomodationProviderListing.acc_provider_id == acc_prov.id).all()
        no_listings = db.query(AccomodationProviderListing).filter(AccomodationProviderListing.acc_provider_id == acc_prov.id).count()

        if no_listings == 0:
            return {
                "status": "success",
                "message": "Accomodation Provider dashboard retrieved successfully",
                "body": {
                    "no_listings": no_listings,
                    "no_likes": 0,
                    "no_reviews": 0,
                    "no_profile_visits": 0
                }
            }

        no_reviews = listings[0].reviews
        no_likes = listings[0].no_likes
        no_profile_visits  = acc_prov.profile_visits

        return {
            "status": "success",
            "message": "Accomodation Provider dashboard retrieved successfully",
            "body": {
                "no_listings": no_listings,
                "no_likes": no_likes,
                "no_reviews": len(no_reviews),
                "no_profile_visits": no_profile_visits
            }
        }

    
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"An error occured while retrieving Accomodation Provider profile: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "An error occured while retrieving Accomodation Provider profile",
                    "body": str(e)
                }
            )
        else:
            raise e


@router.post("/accomodation_provider/home/profile_visits_chart", tags=["Accomodation Provider"])
async def get_profile_visits_trend_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    permits: list = HasPermissionTo("view")
):
    try:
        acc_prov = db.query(AccomodationProvider).filter(AccomodationProvider.user_id == current_user.get('id')).first()

        if acc_prov is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Accomodation Provider profile does not exist",
                    "body": ""
                }
            )

        monthly_visits = {month:0 for month in range(1,13)}
        current_year = str(datetime.now().year)

        profile_visits_data = db.execute("""
        SELECT strftime('%m', visit_date) as visit_month,
            COUNT(*) as no_visits
        FROM Accomodation_Provider_Profile_Visit_Stats
        WHERE acc_provider_id = :provider_id AND strftime('%Y', visit_date) = :current_year
        GROUP BY strftime('%m', visit_date)
    """, {"provider_id": acc_prov.user_id, "current_year": current_year}).fetchall()

        for row in profile_visits_data:
            month, no_visits = row
            monthly_visits[int(month)] = no_visits

        #generate labels for the x-axis (months)
        month_labels = [calendar.month_abbr[i] for i in range(1,13)]
        visits_data = list(monthly_visits.values())

        visit_data = {
            "month_labels": month_labels,
            "visits_data": visits_data
        }

        chart_image = await visualize_profile_visits_chart(visit_data)
        return {
            "status": "success",
            "message": "Profile visits trend data received successfully",
            "body": {
                "chart_image": chart_image
            }
        }


    
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"An error occured while retrieving Accomodation Provider profile visits: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "An error occured while retrieving Accomodation Provider profile visits",
                    "body": str(e)
                }
            )
        else:
            raise e

@router.post("/accomodation_provider/listing/create", tags=["Listing"])
async def create_accom_provider_listing(
    accomodation_name: str = Form(default=None),
	description: str = Form(default=None),
	accomodation_address: str = Form(default=None),
	accomodation_type: ACC_TYPE = Form(default=None),
	number_of_rooms: int = Form(default=None),
	number_of_kitchen: int = Form(default=None),
	number_of_bathrooms: int = Form(default=None),
	state: STATES_DATA_TYPE = Form(default=None),
	city: str = Form(default=None),
    accom_images: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    permits: list = HasPermissionTo("edit")
):
    
    try:
        acc_prov = db.query(AccomodationProvider).filter(AccomodationProvider.user_id == current_user.get('id')).first()
        check_curr_user = db.query(User).filter(User.id == current_user.get('id')).first()
        
        if acc_prov is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Accomodation Provider profile does not exist",
                    "body": ""
                }
            )
        
        if check_curr_user.profile != "Accomodation Provider" and check_curr_user.profile is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "status": "error",
                        "message": "You can't create an Accomodation Provider listing, you are not an Accomodation Provider",
                        "body": ""
                    }
                )
        
        capitalized_city = await capitalize_city(city)
        validated_city = await validate_city(capitalized_city, state)
        image_urls = upload_files_cloud(accom_images)

        
        new_listing = AccomodationProviderListing(
            acc_provider_id = acc_prov.id,
            accomodation_type = accomodation_type,
            accomodation_name = accomodation_name,
            accomodation_address = accomodation_address,
            accomodation_state = state,
            accomodation_city = validated_city,
            accomodation_description = description,
            number_of_rooms = number_of_rooms,
            number_of_bathrooms = number_of_bathrooms,
            number_of_kitchens = number_of_kitchen
)
        
        # file_names, thumbnail_names = await handle_files_upload(accom_images) 
        new_listing.accom_images = image_urls
        # new_listing.images_thumbnail = thumbnail_names

        db.add(new_listing)
        db.commit()
        db.refresh(new_listing)
        

        return {
            "status": "success",
            "message": "Accomodation Provider listing created successfully",
            "body": new_listing
        }
    
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"An error occured while creating Accomodation Provider listing: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "An error occured while creating Accomodation Provider listing",
                    "body": str(e)
                }
            )
        else:
            raise e



@router.get("/accomodation_provider/listing/filter/{listing_id}", tags = ['Listing'])
async def get_listing(
    listing_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    permits: list = HasPermissionTo("view")
):
    try:
        listing = db.query(AccomodationProviderListing).filter(AccomodationProviderListing.id == listing_id).first()
        check_curr_user = db.query(User).filter(User.id == current_user.get('id')).first()
    
        
        if listing is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Accomodation Listing does not exist",
                    "body": ""
                }
            )
        
        check_acc_prov = db.query(AccomodationProvider).filter(AccomodationProvider.id == listing.acc_provider_id).first()
        if check_acc_prov is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "There is no Accomodation Provider with this listing",
                    "body": ""
                }
            )
        
        if check_acc_prov.user_id != current_user.get('id'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "You can't view an Accomodation Provider listing, you are not the owner",
                    "body": ""
                }
            )
        
        if check_curr_user.profile != "Accomodation Provider" and check_curr_user.profile is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "status": "error",
                        "message": "You can't view an Accomodation Provider listing Image, you are not an Accomodation Provider",
                        "body": ""
                    }
                )
        
        return {
            "status": "success",
            "message": "Listing retrieved successfully",
            "body": listing
        }
    
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"An error occured while retrieving listing: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "An error occured while retrieving listing",
                    "body": str(e)
                }
            )
        else:
            raise e

@router.get("/accomodation_provider/listings/filter", tags = ['Listing'])
async def get_all_listings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        check_curr_user = db.query(User).filter(User.id == current_user.get('id')).first()

        if check_curr_user.profile != "Accomodation Provider" and check_curr_user.profile is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "You can't view an Accomodation Provider listing Image, you are not an Accomodation Provider",
                    "body": ""
                }
            )
        check_acc_prov = db.query(AccomodationProvider). \
        filter(AccomodationProvider.user_id == current_user.get('id')).first()

        listings = db.query(AccomodationProviderListing). \
        filter(AccomodationProviderListing.acc_provider_id == check_acc_prov.id).all()

        if check_acc_prov is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Accomodation Provider does not exist",
                    "body": ""
                }
            )

        
        return {
            "status": "success",
            "message": "Listings retrieved successfully",
            "body": listings
        }


    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"An error occured while retrieving listings: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "An error occured while retrieving listings",
                    "body": str(e)
                }
            )
        else:
            raise e


@router.patch("/accomodation_provider/listing/update/{listing_id}", tags = ['Listing'])
async def update_listing(
    listing_id: int,
    accomodation_name: str = Form(default=None),
	description: str = Form(default=None),
	accomodation_address: str = Form(default=None),
	accomodation_type: ACC_TYPE = Form(default=None),
	number_of_rooms: int = Form(default=None),
	number_of_kitchen: int = Form(default=None),
	number_of_bathrooms: int = Form(default=None),
	state: STATES_DATA_TYPE = Form(default=None),
	city: str = Form(default=None),
    accom_images: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    permits: list = HasPermissionTo("edit")
):
    try:

        check_listing_to_update = db.query(AccomodationProviderListing).filter(AccomodationProviderListing.id == listing_id).first()
        check_curr_user = db.query(User).filter(User.id == current_user.get('id')).first()

        if check_listing_to_update is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Listing does not exist",
                    "body": ""
                }
            )
        check_acc_prov = db.query(AccomodationProvider).filter(AccomodationProvider.id == check_listing_to_update.acc_provider_id).first()
        if check_acc_prov.user_id != current_user.get('id'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "You can't update an Accomodation Provider listing, you are not the owner",
                    "body": ""
                }
            )

        if check_curr_user.profile != "Accomodation Provider" and check_curr_user.profile is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "You can't update an Accomodation Provider listing, you are not an Accomodation Provider",
                    "body": ""
                }
            )
        
        capitalized_city = await capitalize_city(city)
        validated_city = await validate_city(capitalized_city, state)
        image_urls = upload_files_cloud(accom_images)
        
        check_listing_to_update.accomodation_name = accomodation_name
        check_listing_to_update.accomodation_address = accomodation_address
        check_listing_to_update.accomodation_type = accomodation_type
        check_listing_to_update.accomodation_state = state
        check_listing_to_update.accomodation_city = validated_city
        check_listing_to_update.accomodation_description = description
        check_listing_to_update.number_of_rooms = number_of_rooms
        check_listing_to_update.number_of_kitchens = number_of_kitchen
        check_listing_to_update.number_of_bathrooms = number_of_bathrooms
        check_listing_to_update.accom_images = image_urls

        # file_names, thumbnail_names  = await handle_files_upload(accom_images)
        # check_listing_to_update.accom_images = file_names

        db.commit()
        db.refresh(check_listing_to_update)

        return {
            "status": "success",
            "message": "Listing updated successfully",
            "body": check_listing_to_update
        }

    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"An error occured while updating Accomodation Listing: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "An error occured while updating Accomodation Listing",
                    "body": str(e)
                }
            )
        else:
            raise e


@router.delete("/accomodation_provider/listing/delete/{listing_id}", tags = ['Listing'])
async def delete_listing(
    listing_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:

        listing_to_delete = db.query(AccomodationProviderListing).filter(AccomodationProviderListing.id == listing_id).first()
        check_curr_user = db.query(User).filter(User.id == current_user.get('id')).first()
        
        if listing_to_delete is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Listing does not exist",
                    "body": ""
                }
            )
        
        check_acc_prov = db.query(AccomodationProvider).filter(AccomodationProvider.id == listing_to_delete.acc_provider_id).first()
        if check_acc_prov.user_id != current_user.get('id'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "You can't delete an Accomodation Provider listing, you are not the owner",
                    "body": ""
                }
            )
        
        if check_curr_user.profile != "Accomodation Provider" and check_curr_user.profile is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "You can't delete an Accomodation Provider listing, you are not an Accomodation Provider",
                    "body": ""
                }
            )
        
        check_user_listing_table = db.query(UserListingLikes).filter(UserListingLikes.listing_id == listing_id).first()
        if check_user_listing_table is not None:
            db.delete(check_user_listing_table)
            db.commit()
        
        db.delete(listing_to_delete)
        db.commit()

        return {
            "status": "success",
            "message": "Listing deleted successfully",
            "body": listing_to_delete
        }
    
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"An error occured while deleting listing: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "An error occured while deleting listing",
                    "body": str(e)
                }
            )
        else:
            raise e
    
