from decouple import config, UndefinedValueError
from passlib.context import CryptContext
from jose import jwt, JWTError
import time
from datetime import datetime, timedelta
from typing import Union,   Any
import logging
from itsdangerous import URLSafeTimedSerializer, BadTimeSignature, SignatureExpired
from fastapi import HTTPException, status
from dotenv import load_dotenv
from pathlib import Path
import secrets
import string
import cloudinary
import cloudinary.uploader as uploader
import hashlib


load_dotenv(dotenv_path=Path('.')/'.env')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SQLALCHEMY_DATABASE_URL = config("DB_PATH")
JSWT_SECRET_KEY = config("JSWT_SECRET_KEY")
JSWT_REFRESH_SECRET_KEY = config("JSWT_REFRESH_SECRET_KEY")
JSWT_ALGORITHM = config("JSWT_ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = config("ACCESS_TOKEN_EXPIRE_MINUTES")
REFRESH_TOKEN_EXPIRE_MINUTES = config("REFRESH_TOKEN_EXPIRE_MINUTES")
ACCESS_TOKEN_EXPIRE_DAYS = config("ACCESS_TOKEN_EXPIRE_DAYS")
API_ENDPOINT = config("API_ENDPOINT")
PROJECT_NAME = config("PROJECT_NAME")
RESET_KEY = config("RESET_KEY")
CLOUDINARY_NAME = config("CLOUDINARY_NAME")
CLOUDINARY_API_KEY = config("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = config("CLOUDINARY_API_SECRET")

password_context = CryptContext(schemes=['bcrypt'], deprecated = "auto")
serializer = URLSafeTimedSerializer(JSWT_SECRET_KEY, salt='Email_Verification_&_Forgot_Password')

cloudinary.config( 
  cloud_name = CLOUDINARY_NAME, 
  api_key = CLOUDINARY_API_KEY, 
  api_secret = CLOUDINARY_API_SECRET 
) 

def signJWT(userID:str):
    num_days = int(ACCESS_TOKEN_EXPIRE_DAYS)*24*60*3600 #converting to seconds
    payload = {
        "userId": userID,
        "expiry": time.time() + num_days,
        "iat": time.time()
    }
    token = jwt.encode(payload, JSWT_SECRET_KEY, algorithm=JSWT_ALGORITHM)
    return {
        "access_token": token
    }


def get_hashed_password(password:str):
    return password_context.hash(password)

def verify_password(password:str, hashed_password:str):
    return password_context.verify(password, hashed_password)

def create_access_token(subject: Union[str, Any], expires_delta: int = None):
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_DAYS)

    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, JSWT_SECRET_KEY, JSWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: Union[str, Any], expires_delta: int = None):
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, JSWT_REFRESH_SECRET_KEY, JSWT_ALGORITHM)
    return encoded_jwt

def decode_JWT(token:str):
    try:
        decoded_token = jwt.decode(
            token, JSWT_SECRET_KEY, algorithms=[JSWT_ALGORITHM]
        )
        return decoded_token
    except jwt.ExpiredSignatureError:
        return {"body": "Signature expired. Please log in again."}
    except jwt.InvalidTokenError:
        return {"body": "Invalid token. Please log in again."}


def get_user_info(user):
    user = user.__dict__
    return {
        "id": user.get('id'),
        "first_name": user.get('first_name'),
        "last_name": user.get('last_name'),
        "email": user.get('email'),
        "is_verified": user.get('is_verified'),
        "profile": user.get('profile'),
        "profile_pic": user.get('profile_picture'),
        "password": user.get('password')
    }

def generate_reset_key(length:int=16):
    alphabets = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabets) for i in range(length))

def generate_password_key(length:int=6):
    alphabets = string.digits
    return ''.join(secrets.choice(alphabets) for i in range(length))

def email_token(email:str):
    _token_ = serializer.dumps(email, salt=JSWT_SECRET_KEY)
    return _token_

def verify_email_token(token:str, max_age:int=3600):
    try:
        email = serializer.loads(token, salt=JSWT_SECRET_KEY, max_age=max_age)
        reset_key = generate_reset_key()
        return {
            "status": "success",
            "message": "Email verified successfully",
            "body": {"email": email,
                    "reset_key": reset_key
                     }
        }
    
    except SignatureExpired:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": "error",
                "message": "Token Expired, please resend verification mail",
                "body": "Token expired" }
        )
    
    except BadTimeSignature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": "error",
                "message": "Invalid Token",
                "body": "Invalid token" }
        )
    except Exception as e:  
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": "error",
                "message": "error verifying token",
                "body": str(e) }
        )

def password_reset_token(email:str):
    _token_ = serializer.dumps(email, salt=JSWT_SECRET_KEY)
    return _token_

def verify_password_reset_token(token: str, max_age: int = 300):
    try:
        # You might want to decode the hashed token back to the original format
        original_token = serializer.loads(token, salt=JSWT_SECRET_KEY, max_age=max_age)
        return {
            "status": "success",
            "message": "Token verified successfully",
            "body": {
                "email": original_token
            }
        }
    
    except SignatureExpired:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": "error",
                "message": "Token Expired, please reset password again",
                "body": "Token expired"
            }
        )
    
    except BadTimeSignature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": "error",
                "message": "Invalid Token",
                "body": "Invalid token"
            }
        )
    except Exception as e:  
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": "error",
                "message": "Error verifying token",
                "body": str(e)
            }
        )

    

def upload_files_cloud(images):

    if isinstance(images, list):
        image_urls = []
        for image in images:
            if image.content_type not in ['image/jpeg', 'image/png']:
                raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Only .Jpeg or .png files are allowed",
                    "body": ""
                }
            )

            uploaded_image = uploader.upload(image.file, folder = "Accom_Services_Uploads/Listings")
            image_url = uploaded_image.get('url')
            image_urls.append(image_url)
        print(image_urls)
        return image_urls
        
    else:
        if images.content_type not in ['image/jpeg', 'image/png']:
            raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "message": "Only .Jpeg or .png files are allowed",
                "body": ""
            }
        )
        uploaded_image = uploader.upload(images.file, folder = "Accom_Services_Uploads/Listings")
        image_url = uploaded_image.get('url')
        return image_url
