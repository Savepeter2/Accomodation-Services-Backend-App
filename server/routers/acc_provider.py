from sqlalchemy.orm import Session
from app.database import engine, get_db
from app.deps import get_current_user
from app.model import User, AccomodationProvider, AccomodationProviderListing
from schemas.acc_prov import (AccomodationProviderSchema, get_states,
                               get_cities, AccomodationProviderListingSchema)
from app.utils import logger
from schemas.user import UserSchema
from fastapi import APIRouter, Body, Depends, status, Response, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
from typing import Literal, List, Tuple
import os
from random import randint
import uuid
from fastapi.encoders import jsonable_encoder
from fastapi import Form
from schemas.acc_prov import ACC_TYPE, STATES_DATA_TYPE
import aiofiles
from PIL import Image
from io import BytesIO
import time
import cv2
import re
import numpy as np
from skimage import io, transform
from io import BytesIO

#from fastapi.responses import JSONResponse

BASEDIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
BASEDIR = os.path.join(BASEDIR, 'app', 'statics', 'media')
BASEDIR = BASEDIR.replace(os.path.sep, os.path.sep + os.path.sep)

print(f"basedir is : {BASEDIR}")

router = APIRouter()

# def make_thumbnail(file,size: tuple = (300, 200)):
#     # Read the image using skimage
#     img = io.imread(file, plugin='matplotlib')
#     # Ensure that the image has 3 channels (RGB)
#     if img.shape[-1] == 4:
#         img = img[:, :, :3]
#     # Resize the image
#     resized_img = transform.resize(img, size, mode='constant')

#     # Convert to uint8 for saving as PNG
#     resized_img = (resized_img * 255).astype(np.uint8)

#     # Save the resized image to BytesIO
#     thumb_io = BytesIO()
#     io.imsave(thumb_io, resized_img, format='png', quality=8)  # Adjust quality as needed
#     thumb_io.seek(0)

#     return thumb_io

async def file_operations(file: UploadFile) -> Tuple[bytes, str, str]:
    root, ext = os.path.splitext(file.filename)
    # img_dir = os.path.join(BASEDIR, 'app\statics\media')
    img_dir = BASEDIR
    if not os.path.exists(img_dir):
        os.makedirs(img_dir)
    content = await file.read()
    if file.content_type not in ['image/jpeg', 'image/png']:
        raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
            "status": "error",
            "message": "Only .Jpeg or .png files are allowed",
            "body": ""
        }
    )
    return content, ext, img_dir
    
def make_thumbnail(file:str, size: tuple = (300, 200)) -> BytesIO:
    img = Image.open(file)
    rgb_im = img.convert('RGB')
    rgb_im.thumbnail(size)

    thumb_io = BytesIO()
    rgb_im.save(thumb_io, format='PNG', quality=85)
    thumb_io.seek(0)
    return thumb_io

async def handle_file_upload(files: List[UploadFile]) -> Tuple[str, str]:
    file_names = []
    thumbnail_names = []
    for file in files:
        content, ext, img_dir = await file_operations(file)

        if not os.path.exists(img_dir):
            os.makedirs(img_dir)

        filepath = os.path.join(img_dir, file.filename)
        async with aiofiles.open(filepath, mode = 'wb') as f:
            await f.write(content)

        new_file = os.path.join(img_dir, file.filename)
        thumbnail_name = f"thumb_{file.filename}"
        thumbnail_content = make_thumbnail(new_file)

        async with aiofiles.open(os.path.join(img_dir, thumbnail_name), mode = 'wb') as f:
            await f.write(thumbnail_content.read())

        file_names.append(file.filename)
        thumbnail_names.append(thumbnail_name)

    return file_names, thumbnail_names
        
            
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
    

@router.post("/accomodation_provider/create", tags=["Accomodation Provider"])
async def create_accom_provider_profile(
    acc_prov_schema: AccomodationProviderSchema, 
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user)
):
    try:
        acc_prov = db.query(AccomodationProvider).filter(AccomodationProvider.id == current_user.get('id')).first()
        check_curr_user = db.query(User).filter(User.id == current_user.get('id') == AccomodationProvider.user_id).first()

        if acc_prov is not None:
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
 
        new_acc_prov = AccomodationProvider(
            brand_name = acc_prov_schema.brand_name,
            phone_number = acc_prov_schema.phone_number,
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


@router.get("/accomodation_provider/profile/{acc_id}", tags=["Accomodation Provider"])
async def get_accom_provider_profile(
    acc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        acc_prov = db.query(AccomodationProvider).filter(AccomodationProvider.user_id == current_user.get('id')).first()
        check_acc_prov = db.query(AccomodationProvider).filter(AccomodationProvider.id == acc_id).first()
        
        if acc_prov is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Accomodation Provider profile does not exist",
                    "body": ""
                }
            )
        
        if check_acc_prov is None:
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

@router.patch("/accomodation_provider/profile/{acc_id}", tags=["Accomodation Provider"])
async def update_accom_provider_profile(
    acc_id: int,
    acc_prov_schema: AccomodationProviderSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        acc_to_update = db.query(AccomodationProvider).filter(AccomodationProvider.user_id == current_user.get('id')).first()
        check_acc_to_update = db.query(AccomodationProvider).filter(AccomodationProvider.id == acc_id).first()

        if acc_to_update is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Accomodation Provider profile not found",
                    "body": ""
                }
            )
        
        if check_acc_to_update is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Accomodation Provider profile not found",
                    "body": ""
                }
            )
        
        capitalized_city = await capitalize_city(acc_prov_schema.city)
        validated_city = await validate_city(capitalized_city, acc_prov_schema.state)

        acc_to_update.brand_name = acc_prov_schema.brand_name
        acc_to_update.phone_number = acc_prov_schema.phone_number
        acc_to_update.brand_address = acc_prov_schema.brand_address
        acc_to_update.state = acc_prov_schema.state
        acc_to_update.city = validated_city
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
 

@router.delete("/accomodation_provider/profile/{acc_id}", tags=["Accomodation Provider"])
async def delete_accom_provider_profile(
    acc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        acc_to_delete = db.query(AccomodationProvider).filter(AccomodationProvider.user_id == current_user.get('id')).first()
        check_acc_to_delete = db.query(AccomodationProvider).filter(AccomodationProvider.id == acc_id).first()
        check_curr_user = db.query(User).filter(User.id == AccomodationProvider.user_id).first()

        if acc_to_delete is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Accomodation Provider profile not found",
                    "body": ""
                }
            )
        
        if check_acc_to_delete is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Accomodation Provider profile not found",
                    "body": ""
                }
            )
        
        #.profile = None
        check_curr_user.profile = None
        db.commit()
        db.refresh(check_curr_user)

        db.delete(check_acc_to_delete)
        db.commit()

        return {
            "status": "success",
            "message": "Accomodation Provider profile deleted successfully",
            "body": check_acc_to_delete
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
    

@router.get("/accomodation_provider/profiles", tags=["Accomodation Provider"])
async def get_all_accom_provider_profiles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        acc_provs = db.query(AccomodationProvider).all()
        return {
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


#ACC PROVIDER ADDING A  LISTING 

@router.post("/accomodation_provider/listing/create", tags=["Accomodation Provider Listing"])
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
    current_user: User = Depends(get_current_user)
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
        capitalized_city = await capitalize_city(city)
        validated_city = await validate_city(capitalized_city, state)
        
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
        
        file_names, thumbnail_names = await handle_file_upload(accom_images)
        print(f"the file names which are uploaded are: {file_names}")
        print(f"the thumbnail names which are uploaded are: {thumbnail_names}")
            
        new_listing.accom_images = file_names
        new_listing.images_thumbnail = thumbnail_names

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


@router.get("/accomodation_provider/listing/{listing_id}/images/show", tags=["Accomodation Provider Listing"])
async def show_listing_images(
    listing_id : int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        check_listing = db.query(AccomodationProviderListing).filter(AccomodationProviderListing.acc_provider_id == current_user.get('id')).first()
        check_listing_id = db.query(AccomodationProviderListing).filter(AccomodationProviderListing.id == listing_id).first()
        
        if check_listing is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Listing does not exist",
                    "body": ""
                }
            )
        
        if check_listing_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Listing does not exist",
                    "body": ""
                }
            )
        listing_images = check_listing.images_thumbnail
        images_path = []
        for image in listing_images:
            images_path.append(f"{BASEDIR}\\{image}")
        print(f"images path: {images_path}")
        # print(f"the listing images are: {listing_images}")
        # for image in listing_images:
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

@router.get("/accomodation_provider/listing/filter/{listing_id}", tags = ['Accomodation Provider Listing'])
async def get_listing(
    listing_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        listing = db.query(AccomodationProviderListing).filter(AccomodationProviderListing.id == listing_id).first()
        check_listing = db.query(AccomodationProviderListing).filter(AccomodationProviderListing.acc_provider_id == current_user.get('id')).first()
        
        if listing is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Accomodation Listing does not exist",
                    "body": ""
                }
            )
        
        if check_listing is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Accomodation Listing does not exist",
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

@router.get("/accomodation_provider/listings/filter", tags = ['Accomodation Provider Listing'])
async def get_all_listings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        listings = db.query(AccomodationProviderListing).all()
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


@router.patch("/accomodation_provider/listing/update/{listing_id}", tags = ['Accomodation Provider Listing'])
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
    current_user: User = Depends(get_current_user)
):
    try:

        check_listing_to_update = db.query(AccomodationProviderListing).filter(AccomodationProviderListing.id == listing_id).first()

        if check_listing_to_update is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Listing does not exist",
                    "body": ""
                }
            )
        
        capitalized_city = await capitalize_city(city)
        validated_city = await validate_city(capitalized_city, state)
        
        check_listing_to_update.accomodation_name = accomodation_name
        check_listing_to_update.accomodation_address = accomodation_address
        check_listing_to_update.accomodation_type = accomodation_type
        check_listing_to_update.accomodation_state = state
        check_listing_to_update.accomodation_city = validated_city
        check_listing_to_update.accomodation_description = description
        check_listing_to_update.number_of_rooms = number_of_rooms
        check_listing_to_update.number_of_kitchens = number_of_kitchen
        check_listing_to_update.number_of_bathrooms = number_of_bathrooms

        file_names = await handle_file_upload(accom_images)
        check_listing_to_update.accom_images = file_names

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


@router.delete("/accomodation_provider/listing/delete/{listing_id}", tags = ['Accomodation Provider Listing'])
async def delete_listing(
    listing_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        listing_to_delete = db.query(AccomodationProviderListing).filter(AccomodationProviderListing.acc_provider_id == current_user.get('id')).first()
        check_listing_to_delete = db.query(AccomodationProviderListing).filter(AccomodationProviderListing.id == listing_id).first()
        
        if listing_to_delete is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Listing does not exist",
                    "body": ""
                }
            )
        
        if check_listing_to_delete is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Listing does not exist",
                    "body": ""
                }
            )
        
        db.delete(check_listing_to_delete)
        db.commit()

        return {
            "status": "success",
            "message": "Listing deleted successfully",
            "body": check_listing_to_delete
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
    
@router.delete("accomodation_provider/listings/delete", tags = ['Accomodation Provider Listing'])
async def delete_all_listings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        listings_to_delete = db.query(AccomodationProviderListing).filter(AccomodationProviderListing.acc_provider_id == current_user.get('id')).all()
        if listings_to_delete is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Listings do not exist",
                    "body": ""
                }
            )
        
        db.delete(listings_to_delete)
        db.commit()

        return {
            "status": "success",
            "message": "Listings deleted successfully",
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





