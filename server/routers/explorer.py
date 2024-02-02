from sqlalchemy.orm import Session, load_only
from app.database import engine, get_db
from app.deps import get_current_user
from app.model import User, AccomodationProviderListing, UserListingLikes, AccomodationProvider, AccomodationProviderProfileVisitStats
from schemas.user import UserSchema
from fastapi import APIRouter, Body, Depends, status, Response, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
from typing import Literal, List, Tuple
from routers.user import HasPermissionTo
import os
import aiofiles
from PIL import Image
from io import BytesIO
from schemas.acc_prov import ACC_TYPE
from fastapi import Form
from sqlalchemy import func
from app.utils import logger



router = APIRouter()

@router.post("/explorer/explore/accomodation_listings", tags = ["Explorer"])
async def explore_all_listings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
    ):

    try:
        check_user = db.query(User).filter(User.id == current_user.get('id')).first()
        accomodation_listings = db.query(AccomodationProviderListing) \
                                            .options(load_only("accomodation_name",
                                                               "accomodation_city",
                                                               "accomodation_state",
                                                               "no_likes",
                                                               "number_of_rooms",
                                                               "accomodation_type",
                                                               "accom_images")).all()

        if not check_user:
            raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "status": "error",
                        "message": "User does not exist",
                        "body": ""
                    }
                )
        
        if check_user.profile != "Explorer":
            raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "status": "error",
                        "message": "User is not an explorer",
                        "body": ""
                    }
                )
        
        return accomodation_listings
    
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


@router.post("/explorer/explore/accomodation_listings/filter/{acc_type}", tags = ["Explorer"])
async def filter_listings(
    acc_type: ACC_TYPE,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    permits: list = HasPermissionTo("view")

    ):

    try:
        check_user = db.query(User).filter(User.id == current_user.get('id')).first()
        filtered_listings = db.query(AccomodationProviderListing).filter(AccomodationProviderListing.accomodation_type == acc_type)\
                                            .options(load_only("accomodation_name",
                                                               "accomodation_city",
                                                               "accomodation_state",
                                                               "no_likes",
                                                               "number_of_rooms",
                                                               "accomodation_type",
                                                               "accom_images")).all()


        if not check_user:
            raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "status": "error",
                        "message": "User does not exist",
                        "body": ""
                    }
                )
        
        if check_user.profile != "Explorer":
            raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "status": "error",
                        "message": "User is not an explorer",
                        "body": ""
                    }
                )
        
        return filtered_listings
    
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
        
@router.post("/explorer/explore/accomodation_listings/{accomodation_listing_id}", tags = ["Explorer"])
async def explore_listing_details(
    accomodation_listing_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    permits: list = HasPermissionTo("view")
    ):

    try:

        check_user = db.query(User).filter(User.id == current_user.get('id')).first()
        accomodation_listing = db.query(AccomodationProviderListing).filter(AccomodationProviderListing.id == accomodation_listing_id).first()
        check_listing = db.query(AccomodationProviderListing).filter(AccomodationProviderListing.id == accomodation_listing_id).first()

        check_acc_provider = db.query(AccomodationProvider).filter \
                            (AccomodationProvider.user_id == accomodation_listing.acc_provider_id).first()
        
        if not check_user:
            raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "status": "error",
                        "message": "User does not exist",
                        "body": ""
                    }
                )
        
        if check_user.profile != "Explorer":
            raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "status": "error",
                        "message": "User is not an explorer",
                        "body": ""
                    }
                )
        
        if not check_listing:
            raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "status": "error",
                        "message": "Accomodation Listing does not exist",
                        "body": ""
                    }
                )
        
        return  {
                "status": "success",
                "message": "Listing details retrieved",
                "body": {"listing_details": accomodation_listing
                                     }
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


@router.post("/explorer/explore/accomodation_listings/{accomodation_listing_id}/agent_details", 
                tags = ["Explorer"])
async def explore_listing_agent_details(
    accomodation_listing_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    permits: list = HasPermissionTo("view")
    ):

    try:
        check_user = db.query(User).filter(User.id == current_user.get('id')).first()

        accomodation_listing = db.query(AccomodationProviderListing).filter(AccomodationProviderListing.id == accomodation_listing_id).first()

        if not check_user:
            raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "status": "error",
                        "message": "User does not exist",
                        "body": ""
                    }
                )
        

        
        if check_user.profile != "Explorer":
            raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "status": "error",
                        "message": "User is not an explorer",
                        "body": ""
                    }
                )
        
        if accomodation_listing is None:
            raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "status": "error",
                        "message": "Accomodation Listing does not exist",
                        "body": ""
                    }
                )
        
        check_acc_provider = db.query(AccomodationProvider).filter \
                            (AccomodationProvider.id == accomodation_listing.acc_provider_id).first()

        
        check_acc_provider.profile_visits += 1
        db.commit()
        new_visit_stat = AccomodationProviderProfileVisitStats(
                acc_provider_id = accomodation_listing.acc_provider_id,
                user_explorer_id = current_user.get('id'),
                profile_visit = 1,
                visit_date = func.now()
            )
        db.add(new_visit_stat)
        db.commit()
        db.refresh(new_visit_stat)

        db.refresh(check_acc_provider)
        db.refresh(accomodation_listing)
        
        return  {
            "status": "success",
                "message": "Listing details retrieved",
                "body": {"listing_details": accomodation_listing,
                          "agent_details": check_acc_provider
                }
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
        

@router.post("/explorer/explore/accomodation_listings/{accomodation_listing_id}/like", tags = ["Explorer"])
async def like_listing(
    accomodation_listing_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    permits: list = HasPermissionTo("edit")
    ):

    try:
    
        check_user = db.query(User).filter(User.id == current_user.get('id')).first()
        check_listing = db.query(AccomodationProviderListing).filter(AccomodationProviderListing.id == accomodation_listing_id).first()
        check_user_listing_like = db.query(UserListingLikes).filter(UserListingLikes.user_id == current_user.get('id')).filter(UserListingLikes.listing_id == accomodation_listing_id).first()

        if not check_user:
            raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "status": "error",
                        "message": "User does not exist",
                        "body": ""
                    }
                )
        
        if check_user.profile != "Explorer":
            raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "status": "error",
                        "message": "User is not an explorer",
                        "body": ""
                    }
                )
        
        if not check_listing:
            raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "status": "error",
                        "message": "Accomodation Listing does not exist",
                        "body": ""
                    }
                )
        
        if check_user_listing_like:
            raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "status": "error",
                        "message": "Listing already liked",
                        "body": ""
                    }
                )
        
        check_listing.no_likes += 1

        user_listing_like = UserListingLikes(
            user_id = current_user.get('id'),
            listing_id = accomodation_listing_id,
            liked = True
        )
        db.add(user_listing_like)
        db.commit()
        db.refresh(check_listing)

        return {
            "status": "success",
            "message": "Listing liked",
            "body": check_listing
        }
    
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"An error occured while trying to like a listing: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "An error occured while trying to like a listing",
                    "body": str(e)
                }
            )
        else:
            raise e


@router.post('/explorer/explore/accomodation_listings/{accomodation_listing_id}/add_review', tags = ["Explorer"])
async def add_review(
    accomodation_listing_id: int,
    review: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    permits: list = HasPermissionTo("edit")
    ):

    try:
    
        check_user = db.query(User).filter(User.id == current_user.get('id')).first()
        check_listing = db.query(AccomodationProviderListing).filter(AccomodationProviderListing.id == accomodation_listing_id).first()

        if not check_user:
            raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "status": "error",
                        "message": "User does not exist",
                        "body": ""
                    }
                )
        
        if check_user.profile != "Explorer":
            raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "status": "error",
                        "message": "User is not an explorer",
                        "body": ""
                    }
                )
        
        if not check_listing:
            raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "status": "error",
                        "message": "Accomodation Listing does not exist",
                        "body": ""
                    }
                )
        reviews = check_listing.reviews
        reviews.append(review)
        db.commit()
        db.refresh(check_listing)

        return {
            "status": "success",
            "message": "Review added",
            "body": check_listing
        }
    
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"An error occured while trying to add a review to a listing: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "An error occured while trying to add a review to a listing",
                    "body": str(e)
                }
            )
        else:
            raise e



    

    
