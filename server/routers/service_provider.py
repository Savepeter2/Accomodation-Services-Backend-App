from sqlalchemy.orm import Session
from app.database import engine, get_db
from app.deps import get_current_user
from app.model import User, ServiceProvider 
from schemas.acc_prov import get_states, get_cities
from schemas.service_provider import ServiceProviderSchema, ServiceProviderOutSchema
from schemas.user import ProfileUpdateSchema
from app.utils import logger
from schemas.user import UserSchema
from fastapi import APIRouter, Body, Depends, status, Response, HTTPException
from typing import Literal
#from fastapi.responses import JSONResponse


router = APIRouter()

@router.post("/service_provider/create", tags=["service_provider"])
async def create_service_provider(
    service_provider: ServiceProviderSchema,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user)
):
    """
    Create a service provider
        """
    try:
        check_serv_provider = db.query(ServiceProvider).filter(ServiceProvider.id == current_user.get('id')).first()
        check_current_user = db.query(User).filter(User.id == current_user.get('id')).first()

        if check_serv_provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Service provider already exists",
                    "body": ""
                }
            )
        if check_current_user.profile != "Service Provider" and check_current_user.profile is not None:
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "You can't create a Service Provider Profile, you didn't sign up as a Service Provider",
                    "body": ""
                }
            )

        new_service_provider = ServiceProvider(
            brand_name = service_provider.brand_name,
            Area_Of_Specialization = service_provider.Area_Of_Specialization,
            phone_number = service_provider.phone_number,
            brand_address = service_provider.brand_address,
            city = service_provider.city,
            state = service_provider.state,
            user_id = current_user.get('id')
        )

        check_current_user.profile = "Service Provider"
        db.commit()
        db.refresh(check_current_user)

        db.add(new_service_provider)
        db.commit()
        db.refresh(new_service_provider)

        return {
            "status": "success",
            "message": "Service Provider created successfully",
            "body": new_service_provider
        } 
    
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"Error creating service provider: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "Internal server error",
                    "body": str(e)
                }
            )
        else:
            raise e
        
@router.get("/service_provider/{id}", tags=["service_provider"])
async def get_service_provider(
    id: int,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user)
):
    """
    Get a service provider
        """
    try:
        check_service_provider = db.query(ServiceProvider).filter(ServiceProvider.id == id).first()
        check_sp = db.query(ServiceProvider).filter(ServiceProvider.user_id == current_user.get('id')).first()

        if not check_service_provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Service Provider does not exist",
                    "body": ""
                }
            )
        
        if check_sp is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "You can't view a Service Provider Profile, you didn't sign up as a Service Provider",
                    "body": ""
                }
            )
        
        return {
            "status": "success",
            "message": "Service Provider found",
            "body": check_service_provider
        }
    
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"Error getting service provider: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "Internal server error",
                    "body": str(e)
                }
            )
        else:
            raise e



@router.patch("/service_provider/{id}", tags=["service_provider"])
async def update_service_provider(
    id: int,
    service_provider: ServiceProviderSchema,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user)
):
    """
    Update a service provider
        """
    try:
        check_service_provider = db.query(ServiceProvider).filter(ServiceProvider.id == id).first()
        check_sp = db.query(ServiceProvider).filter(ServiceProvider.user_id == current_user.get('id')).first()

        if not check_service_provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Service Provider does not exist",
                    "body": ""
                }
            )
        
        if check_sp is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "You can't update a Service Provider Profile, you didn't sign up as a Service Provider",
                    "body": ""
                }
            )
        
        check_service_provider.brand_name = service_provider.brand_name
        check_service_provider.Area_Of_Specialization = service_provider.Area_Of_Specialization
        check_service_provider.phone_number = service_provider.phone_number
        check_service_provider.brand_address = service_provider.brand_address
        check_service_provider.city = service_provider.city
        check_service_provider.state = service_provider.state

        db.commit()
        db.refresh(check_service_provider)
        
        return {
            "status": "success",
            "message": "Service Provider updated successfully",
            "body": check_service_provider
        }
    
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"Error updating service provider: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "Internal server error",
                    "body": str(e)
                }
            )
        else:
            raise e


@router.delete("/service_provider/{id}", tags=["service_provider"])
async def delete_service_provider(
    id: int,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user)
):
    """
    Delete a service provider
        """
    try:
        check_service_provider = db.query(ServiceProvider).filter(ServiceProvider.id == id).first()
        check_sp = db.query(ServiceProvider).filter(ServiceProvider.user_id == current_user.get('id')).first()
        check_curr_user = db.query(User).filter(User.id == ServiceProvider.user_id == current_user.get('id')).first()


        if not check_service_provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Service Provider does not exist",
                    "body": ""
                }
            )
        
        if check_sp is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "You can't delete a Service Provider Profile, you didn't sign up as a Service Provider",
                    "body": ""
                }
            )
        
        check_curr_user.profile = None
        db.commit()
        db.refresh(check_curr_user) 

        db.delete(check_service_provider)
        db.commit()

        return {
            "status": "success",
            "message": "Service Provider deleted successfully",
            "body": check_service_provider
        }
    
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"Error deleting service provider: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "Internal server error",
                    "body": str(e)
                }
            )
        else:
            raise e

@router.get("/service_provider", tags=["service_provider"])
async def get_all_service_providers(
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user)
):
    """
    Get all service providers
        """
    try:
        check_sp = db.query(ServiceProvider).filter(ServiceProvider.user_id == current_user.get('id')).first()

        if check_sp is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "You can't view a Service Provider Profile, you didn't sign up as a Service Provider",
                    "body": ""
                }
            )
        
        service_providers = db.query(ServiceProvider).all()
        
        return {
            "status": "success",
            "message": "Service Providers found",
            "body": service_providers
        }
    
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"Error getting service providers: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "Internal server error",
                    "body": str(e)
                }
            )
        else:
            raise e




    



    