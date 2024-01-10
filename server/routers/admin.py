
from fastapi import APIRouter, Body, Depends, status, Response, HTTPException
from app.deps import get_current_user
from schemas.user import PROFILE_DATA_TYPE
from fastapi import UploadFile, Form, File
from sqlalchemy.orm import Session
from app.database import engine, get_db
from  app.model import User
from app.utils import get_user_info
from app.utils import logger, upload_files_cloud
from sqlalchemy.orm import Session
from app.database import engine, get_db
from app.deps import get_current_user
from app.model import User, AccomodationProvider, AccomodationProviderListing, func, AccomodationProviderProfileVisitStats
from schemas.acc_prov import (AccomodationProviderSchema, get_states,
                               get_cities, AccomodationProviderListingSchema)
from routers.user import HasPermissionTo
from fastapi.responses import FileResponse
import os
from random import randint
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse
from fastapi import Form
from schemas.acc_prov import ACC_TYPE, STATES_DATA_TYPE
import aiofiles
from PIL import Image
from io import BytesIO
from datetime import datetime
import calendar
import matplotlib.pyplot as plt
from routers.acc_provider import capitalize_city, validate_city, validate_phone_number, visualize_profile_visits_chart

BASEDIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
BASEDIR = os.path.join(BASEDIR, 'app', 'statics', 'media')
BASEDIR = BASEDIR.replace(os.path.sep, os.path.sep + os.path.sep)

router = APIRouter()

#updating the profile of the user
@router.patch('/user/update/{user_id}', tags=['Admin'])
async def update_user_profile(
    user_id:int,
    user_profile: PROFILE_DATA_TYPE,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    permits: list = HasPermissionTo("update_user")
):
    """
    This endpoint is just used to update the profile between 
    ["Accomodation Provider" or "Explorer"] of the user

    """
    try:
        user_to_update = db.query(User).filter(User.id == user_id).first()
        check_curr_user = db.query(User).filter(User.id == current_user.get('id')).first()

        if user_to_update is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "User does not exist",
                    "body": ""
                }
            )
        
        if check_curr_user.principal != "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Only admin can update user profile",
                    "body": ""
                }
            )
        
        user_to_update.profile = user_profile

        db.commit()
        db.refresh(user_to_update)

        return {
            "status": "success",
            "message": "User updated successfully",
            "body": get_user_info(user_to_update)
        }
    
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"user: Error updating user {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "Error updating user",
                    "body": str(e)
                }
            )
        else:
            raise e
        

@router.get("/accomodation_provider/profile/filter/{acc_id}", tags=["Admin"])
async def get_accom_provider_profile(
    acc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    permits: list = HasPermissionTo("view")
):
    try:
        acc_prov = db.query(AccomodationProvider).filter(AccomodationProvider.id == acc_id).first()
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
        
        if check_curr_user.principal != "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Only admin can retrieve Accomodation Provider profile",
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



@router.patch("/accomodation_provider/profile/update/{acc_prof_id}", tags=["Admin"])
async def update_accom_provider_profile(
    acc_prof_id: int ,
    brand_name: str = Form(default=None) ,
	phone_number: str = Form(default=None),
	brand_address: str = Form(default=None),
	state: STATES_DATA_TYPE = Form(default=None) ,
	city: str = Form(default=None),
    profile_picture : UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    permits: list = HasPermissionTo("update_user")
):
    try:
        acc_to_update = db.query(AccomodationProvider).filter(AccomodationProvider.id == acc_prof_id).first()
        check_curr_user = db.query(User).filter(User.id == current_user.get('id')).first()
        
        if acc_to_update is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Accomodation Provider profile not found",
                    "body": ""
                }
            )
        
        if check_curr_user.principal != "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Only admin can update Accomodation Provider profile",
                    "body": ""
                }
            )
        
        capitalized_city = await capitalize_city(city)
        validated_city = await validate_city(capitalized_city, state)
        # image_name, thumbnail_name = await image_upload(profile_picture)
        image_url = upload_files_cloud(profile_picture)
        validated_phone_num = await validate_phone_number(phone_number)


        acc_to_update.brand_name = brand_name
        acc_to_update.phone_number = validated_phone_num
        acc_to_update.brand_address = brand_address
        acc_to_update.state = state
        acc_to_update.city = validated_city
        # acc_to_update.acc_prov_picture = image_name
        # acc_to_update.acc_prov_thumbnail_picture = thumbnail_name
        acc_to_update.phone_number = validated_phone_num
        acc_to_update.profile_picture_url = image_url

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
        
        
@router.get("/accomodation_provider/filter/profiles", tags=["Admin"])
async def get_all_accom_provider_profiles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    permits: list = HasPermissionTo("view_all")
):
    try:
        acc_provs = db.query(AccomodationProvider).all()
        check_curr_user = db.query(User).filter(User.id == current_user.get('id')).first()

        if check_curr_user.principal != "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Only admin can retrieve Accomodation Provider profiles",
                    "body": ""
                }
            )
        
        return      {
            "status": "success",
            "message": "Accomodation Provider profiles retrieved successfully",
            "body": acc_provs
                }
    
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"An error occured while retrieving Accomodation Provider profiles: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "An error occured while retrieving Accomodation Provider profiles",
                    "body": str(e)
                }
            )
        else:
            raise e
        

@router.get("/accomodation_provider/{acc_id}/home", tags=["Admin"])
async def accom_provider_dashboard(
    acc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    permits: list = HasPermissionTo("view")
):
    
    try:
        acc_prov = db.query(AccomodationProvider).filter(AccomodationProvider.id == acc_id).first()
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
        
        if check_curr_user.principal != "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Only admin can retrieve Accomodation Provider dashboard",
                    "body": ""
                }
            )
        
        listings = db.query(AccomodationProviderListing).filter(AccomodationProviderListing.acc_provider_id == acc_id).all()
        no_listings = db.query(AccomodationProviderListing).filter(AccomodationProviderListing.acc_provider_id == acc_id).count()

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

@router.delete("/accomodation_provider/profile/delete/{acc_id}", tags=["Admin"])
async def delete_accom_provider_profile(
    acc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    permits: list = HasPermissionTo("delete")
):
    try:
        acc_to_delete = db.query(AccomodationProvider).filter(AccomodationProvider.id == acc_id).first()
        check_curr_user = db.query(User).filter(User.id == current_user.get('id')).first()

        if acc_to_delete is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Accomodation Provider profile not found",
                    "body": ""
                }
            )
        
        if check_curr_user.principal != "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Only admin can delete Accomodation Provider profile",
                    "body": ""
                }
            )

        acc_to_delete.profile = None
        db.commit()
        db.refresh(acc_to_delete)

        db.delete(acc_to_delete)
        db.commit()

        return {
            "status": "success",
            "message": "Accomodation Provider profile deleted successfully",
            "body": acc_to_delete
        }
    
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"An error occured while deleting Accomodation Provider profile: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "An error occured while deleting Accomodation Provider profile",
                    "body": str(e)
                }
            )
        else:
            raise e


@router.post("/accomodation_provider/{acc_id}/home/profile_visits_chart", tags=["Admin"])
async def get_profile_visits_trend_data(
    acc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    permits: list = HasPermissionTo("view")
):
    try:
        acc_prov = db.query(AccomodationProvider).filter(AccomodationProvider.id == acc_id).first()
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
        
        if check_curr_user.principal != "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Only admin can retrieve Accomodation Provider profile visits",
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



@router.get("/accomodation_provider/listing/{listing_id}/images/show", tags=["Admin"])
async def show_listing_images(
    listing_id : int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    permits: list = HasPermissionTo("view")
):
    try:
        check_listing = db.query(AccomodationProviderListing).filter(AccomodationProviderListing.id == listing_id).first()
        check_curr_user = db.query(User).filter(User.id == current_user.get('id')).first()

        if check_listing is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Listing does not exist",
                    "body": ""
                }
            )
        
        if check_curr_user.principal != "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Only admin can retrieve listing images",
                    "body": ""
                }
            )

        listing_images = check_listing.images_thumbnail
        images_path = []
        for image in listing_images:
            images_path.append(f"{BASEDIR}\\{image}")
        print(f"images path: {images_path}")
        return FileResponse(images_path[1])
        
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"An error occured while retrieving listing images: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "Listing images not found",
                    "body": str(e)
                }
            )
        else:
            raise e



@router.delete("/accomodation_provider/listings/delete", tags = ['Admin'])
async def delete_all_listings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    permits: list = HasPermissionTo("delete")
):
    try:
        listings_to_delete = db.query(AccomodationProviderListing).all()
        check_curr_user = db.query(User).filter(User.id == current_user.get('id')).first()

        if check_curr_user.principal != "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Only admin can delete listings",
                    "body": ""
                }
            )
        
        db.delete(listings_to_delete)
        db.commit()

        return {
            "status": "success",
            "message": "All Listings deleted successfully",
            "body": listings_to_delete
        }
    
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"An error occured while deleting listings: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "An error occured while deleting listings",
                    "body": str(e)
                }
            )
        else:
            raise e

