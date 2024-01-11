from sqlalchemy.orm import Session
from app.database import engine, get_db
from app.utils import (
     get_hashed_password, get_user_info, 
     verify_password, signJWT, logger,
     email_token,
     verify_email_token,
     API_ENDPOINT,
     PROJECT_NAME,
     generate_reset_key,
     generate_password_key,
    upload_files_cloud,
    password_reset_token,
    verify_password_reset_token


)
from app.acl import check_permission,valid_permissions
from app.deps import get_current_user
from app.mailer_utils import send_token_email
from schemas.user import UserSchema, UserUpdateSchema, EmailSchema, ProfileUpdateSchema, HasPermissionTo
from fastapi import APIRouter, Body, Depends, status, Response, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from typing import Literal
from  app.model import User
from fastapi.responses import JSONResponse
from schemas.user import PROFILE_DATA_TYPE
from fastapi import UploadFile, Form, File, Request
# from routers.acc_provider import image_upload
from pydantic import EmailStr


router = APIRouter()



@router.post('/user/signup', tags =['User'])
async def create_user(
    user: UserSchema,
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        check_user = db.query(User).filter(User.email == user.email).first()
        if check_user is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "User with this email already exists",
                    "body": ""
                }
            )
        hashed_password = get_hashed_password(user.password)
        password = user.password
        confirm_password = user.confirm_password
        if password != confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Password and confirm password do not match",
                    "body": ""
                }
            )

        token = email_token(user.email)

        email_verification_endpoint = f'{API_ENDPOINT}/user/confirm-email/{token}'
        mail_body = {
            'email': user.first_name,
            'project_name': PROJECT_NAME,
            'url': email_verification_endpoint
        }

        mail_token = await send_token_email(subject = "Email Verification: Registration Confirmation", 
                                      email_to=user.email,
                                      body=mail_body,
                                      template='email_verification.html')
        
        success_mail = mail_token['status']
        if success_mail == 'success':
            new_user = User(
                first_name = user.first_name,
                last_name = user.last_name,
                email = user.email,
                password = hashed_password,
                profile = user.profile
        )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)

            return {
            "status": "success",
            "message": "User created successfully",
            "body": get_user_info(new_user) | signJWT(user.email) | mail_token
        }

        if success_mail == 'success':
            return {
            "status": "success",
            "message": "Email verification link has been sent successfully to your email, please kindly click on the link to verify your email",
        "body": ""
            }

    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"error creating user {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "Error creating user",
                    "body": str(e)
                }
            )
        else:
            raise e


@router.get("/user/confirm-email/{token}", tags=["User"])
async def user_verification(
    token:str,
    db: Session = Depends(get_db)
):
    try:
        token_data = verify_email_token(token)
        user = db.query(User).filter(User.email == token_data['body']['email']).first() #the token_data['body'] is the email
        reset_key = token_data['body']['reset_key']
        print(token_data)

        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Invalid token",
                    "body": ""
                }
            )
        
        if user.key_flag == True:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "User already verified, kindly proceed to login",
                    "body": ""
                }
            )
        
        user.key = reset_key
        user.key_flag = True    
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": f"User with this email: {user.email} does not exist",
                    "body": ""
                }
            )
        
        user.is_verified = True
        db.commit()
        db.refresh(user)
        return {
            "status": "success",
            "message": "User verified successfully, kindly proceed to login",
            # "body": get_user_info(user)
        }
    
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"error verifying user {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "Error verifying user",
                    "body": ""
                }
            )
        else:
            raise e


@router.post('/user/resend-verification-email', tags=['User'])
async def resend_verification_email(
    email:str,
    db: Session = Depends(get_db)
):
    try:
        check_user = db.query(User).filter(User.email == email).first()
        if check_user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "User does not exist",
                    "body": ""
                }
            )
        token = email_token(email)
        print(token)

        email_verification_endpoint = f'{API_ENDPOINT}/user/confirm-email/{token}'
        mail_body = {
            'email': email,
            'project_name': PROJECT_NAME,
            'url': email_verification_endpoint
        }

        mail_status = await send_token_email(
         subject="Email Verification: Registration Confirmation"  ,
            email_to=email,
            body=mail_body,
            template='email_verification.html' 
        )

        if mail_status['status'] == 'success':
            return {
                "status": "success",
                "message": "mail for Email verification has been sent successfully",
                "body": ""
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "Error sending email",
                    "body": ""
                }
            )
        
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"error resending verification email {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "Error resending verification email",
                    "body": str(e)
                }
            )
        else:
            raise e
        

@router.post('/user/forgot-password', tags=['User'])
async def forgot_password(
    email: EmailStr,
    db: Session = Depends(get_db)
):
    try:
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "User does not exist",
                    "body": ""
                }
            )
        reset_key = password_reset_token(email)

        mail_body = {
            'email': email,
            'project_name': PROJECT_NAME,
            'reset_key': reset_key
        }

        mail_status = await send_token_email(
            subject="Password Reset",
            email_to=email,
            body=mail_body,
            template='reset_password.html'
        )

        if mail_status['status'] == 'success':
            return {
                "status": "success",
                "message": "mail for password reset has been sent successfully",
                "body": ""
            }
        elif mail_status['status'] == 'error':
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "Error sending email",
                    "body": ""
                }
            )

    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"error sending password reset email {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "Error sending password reset email",
                    "body": str(e)
                }
            )
        else:
            raise e


@router.post('/user/reset-password/', tags=['User'])
async def reset_password(
    email: EmailSchema,
    new_password: str,
    confirm_password: str,
    password_reset_token:str,
    db: Session = Depends(get_db)
):
    """
    This endpoint is used to change the password of the user, if the user has forgotten the password
    """
    try:
        user = db.query(User).filter(User.email == email.email).first()
        user_password = user.password
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "User does not exist",
                    "body": ""
                }
            )
        
        token_data = verify_password_reset_token(password_reset_token)
        check_user = db.query(User).filter(User.email == token_data['body']['email']).first() #the token_data['body'] is the email

        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Invalid password reset token",
                    "body": ""
                }
            )
        
        if not check_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": f"User with this email: {check_user.email} does not exist",
                    "body": ""
                }
            )
        
        if verify_password(new_password, user_password):
            logger.error("user: new password cannot be equal to old password.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "new password cannot be equal to old password.",
                    "body": ""
                }
            )
        
        if new_password != confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Password and confirm password do not match",
                    "body": ""
                }
            )
        hashed_password = get_hashed_password(new_password)
        user.password = hashed_password
        db.commit()
        db.refresh(user)
        return {
            "status": "success",
            "message": "Password changed successfully",
            "body": ""
        }
    
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"error changing password {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "Error changing password",
                    "body": str(e)
                }
            )
        else:
            raise e


@router.post('/user/login', tags = ['User'])
async def user_login(
    login_data: OAuth2PasswordRequestForm = Depends(),
    db:Session = Depends(get_db)
):
    try:
        user = db.query(User).filter(login_data.username == User.email).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Incorrect login details, email does not exist. Please signup.",
                    "body": ""
                }
            )
        hashed_password = user.password
        if not verify_password(login_data.password, hashed_password):
            logger.error("user: Incorrect login details, old password is incorrect.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Incorrect login details, old password is incorrect.",
                    "body": ""
                }
            )
        return {
            "status": "success",
            "message": "User has been logged in successfully",
            "body": get_user_info(user) | signJWT(user.email)
        } | signJWT(user.email)
    
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"user: Error logging in user:  {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "Error logging in user",
                    "body": str(e)
                }
            )
        else:
            raise e


@router.post('/user/logout', tags=['User'])
async def user_logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        response = JSONResponse(content={"message": "Logged out successfully"})
        response.delete_cookie("access_token_cookie")
        response.delete_cookie(key = "Authorization")

        return {
            "status": "success",
            "message": "User has been logged out successfully",
            "body": current_user
        }
    
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"user: Error logging out user {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "Error logging out user",
                    "body": str(e)
                }
            )
        else:
            raise e
        
# #updating the password of the user
# @router.patch('/user/update/{user_id}', tags=['user'])
# async def update_user(
#     user_id:int,
#     user:UserUpdateSchema,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):  
#     """
#     this endpoint is basically updating the password of the user
#     """
#     try:
#         user_to_update = db.query(User).filter(User.id == user_id).first()

#         if user_to_update is None:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail={
#                     "status": "error",
#                     "message": "User does not exist",
#                     "body": ""
#                 }
#             )
        
#         if not verify_password(user.old_password, user_to_update.password):
#             logger.error("user: Incorrect login details, old password is incorrect.")
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail={
#                     "status": "error",
#                     "message": "Incorrect login details, old password is incorrect.",
#                     "body": ""
#                 }
#             )
#         # hash_old_password = get_hashed_password(user.old_password)
#         elif verify_password(user.new_password, user_to_update.password):
#             logger.error("user: new password cannot be equal to old password.")
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail={
#                     "status": "error",
#                     "message": "new password cannot be equal to old password.",
#                     "body": ""
#                 }
#             )
        
#         hashed_password = get_hashed_password(user.new_password)
#         user_to_update.password = hashed_password
#         db.commit()
#         db.refresh(user_to_update)

#         return {
#             "status": "success",
#             "message": "User updated successfully",
#             "body": get_user_info(user_to_update)
#         }
    
#     except Exception as e:
#         if not isinstance(e, HTTPException):
#             logger.error(f"user: Error updating user {e}")
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail={
#                     "status": "error",
#                     "message": "Error updating user",
#                     "body": str(e)
#                 }
#             )
#         else:
#             raise e
        
@router.delete('/user/delete/{user_id}', tags=['User'])
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    permits: list = HasPermissionTo("delete"),
):
    try:
        user_to_delete = db.query(User).filter(User.id == user_id).first()
        if user_to_delete is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "User does not exist",
                    "body": ""
                }
            )
        db.delete(user_to_delete)
        db.commit()
        return {
            "status": "success",
            "message": "User deleted successfully",
            "body": user_to_delete
        }
    
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"user: Error deleting user {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "Error deleting user",
                    "body": str(e)
                }
            )
        else:
            raise e


@router.get('/user/filter/{user_id}', tags=['User'])
async def get_user(
    user_id: int,
    current_user: UserSchema = Depends(get_current_user),
    db: Session = Depends(get_db),
     permits: list = HasPermissionTo("view")
):
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "User does not exist",
                    "body": ""
                }
            )
        return {
            "status": "success",
            "message": "User retrieved successfully",
            "body": get_user_info(user)
        }
    
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"user: Error retrieving user {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "Error retrieving user",
                    "body": str(e)
                }
            )
        else:
            raise e

@router.get('/user/all', tags=['User'])
async def get_all_users(
    current_user: UserSchema = Depends(get_current_user),
    db: Session = Depends(get_db),
    permits: list = HasPermissionTo("view_all")
):
    try:
        users = db.query(User).all()
        return {
            "status": "success",
            "message": "Users retrieved successfully",
            "body": users
        }
    
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"user: Error retrieving users {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "Error retrieving users",
                    "body": str(e)
                }
            )
        else:
            raise e

@router.get('/user/me', tags = ['User'])
async def get_current_user_info(
    current_user: UserSchema = Depends(get_current_user),
    db: Session = Depends(get_db),
    permits: list = HasPermissionTo("view")
):
    try:
        return {
            "status": "success",
            "message": "User retrieved successfully",
            "body": current_user
        }
    
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"user: Error retrieving user {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "Error retrieving user",
                    "body": str(e)
                }
            )
        else:
            raise e


@router.patch('/user/update_permission',  tags=["User"])
async def update_permission(
    email: EmailStr,
    permission: valid_permissions = "user",
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user),
    permits: list = HasPermissionTo("update_permission")
):

    try:
        user_to_update = db.query(User).filter(User.email == email).first()
        user_to_update.principal = check_permission(permission)

        db.commit()
        db.refresh(user_to_update)

        return {
            "status": "success",
            "message": "User permission updated successfully",
            "body": user_to_update.__dict__
        }

    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"user: Error updating user permission {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "Error updating user permission",
                    "body": str(e)
                }
            )
        else:
            raise e

@router.patch("/user/{id}/profile/update", tags=["User"])
async def update_user_profile(
    id: int,
    first_name: str = Form(default=None),
    last_name: str = Form(default=None),
    profile_picture: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user),
    permits: list = HasPermissionTo("update_user")
):
    """
    Update a user profile, for updating first name, last name and profile picture of the user[explorer]
        """
    try:
        check_user = db.query(User).filter(id == current_user.get('id')).first()
        
        if not check_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "User does not exist",
                    "body": ""
                }
            )
        
        if check_user.profile != "Explorer" and check_user.profile is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "You are not an explorer, you cannot update your profile",
                    "body": ""
                }
            )
        # image_name, thumbnail_name = await image_upload(profile_picture)
        image_url = upload_files_cloud(profile_picture)

        check_user.first_name = first_name
        check_user.last_name = last_name
        check_user.profile_picture_url = image_url
        
        db.commit()
        db.refresh(check_user)
        
        return {
            "status": "success",
            "message": "User profile updated successfully",
            "body": check_user
        }
    
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"Error updating user profile: {e}")
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










        
        
