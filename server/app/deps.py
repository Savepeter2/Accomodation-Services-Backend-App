from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordBearer
from app.model import User
from pydantic import BaseModel, ValidationError
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db

from .utils import(
    jwt,
    JWTError,
    JSWT_ALGORITHM,
    JSWT_SECRET_KEY
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/login")  

class SystemUser(BaseModel):
    password: str


def get_current_user(token:str = Depends(oauth2_scheme), db: Session = Depends(get_db)):

    try:
        token_data = jwt.decode(
            token, JSWT_SECRET_KEY, algorithms=[JSWT_ALGORITHM]
        )
        if datetime.fromtimestamp(token_data['expiry']) < datetime.now():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": "error",
                "message": "Token Expired, please login again",
                "body": "Token expired" }
            )
        
    except (jwt.JWTError, ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Invalid Credentials: ", 
                    "body": str(e)},
            headers={"WWW-Authenticate": "Bearer"}

        )
    user = db.query(User).filter(User.email == token_data['userId']).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": "error",
                "message": "User not found, please ensure you are logged in",
                "body": "User not found"
            }

        )

    return user.__dict__





