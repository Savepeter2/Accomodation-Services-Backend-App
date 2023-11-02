from re import TEMPLATE
from fastapi_mail import FastMail, MessageSchema,ConnectionConfig
from fastapi import HTTPException, status
from fastapi_mail.email_utils import DefaultChecker
from pydantic import EmailStr
from dotenv import load_dotenv
from fastapi_mail.errors import ConnectionErrors
from pathlib import Path
from decouple import config
import os

load_dotenv(dotenv_path=Path('.')/'.env')

MAIL_USER_NAME = config("MAIL_USER_NAME")
MAIL_PASSWORD = config("MAIL_PASSWORD")
MAIL_FROM = config("MAIL_FROM")
MAIL_PORT = config("MAIL_PORT")
MAIL_SERVER = config("MAIL_SERVER")
MAIL_TLS = config("MAIL_TLS")
MAIL_SSL = config("MAIL_SSL")

config = ConnectionConfig(
    MAIL_USERNAME=MAIL_USER_NAME,
    MAIL_PASSWORD=MAIL_PASSWORD,
    MAIL_FROM=MAIL_FROM,
    MAIL_PORT=MAIL_PORT,
    MAIL_SERVER=MAIL_SERVER,
    MAIL_TLS=True,
    MAIL_SSL=False,
    # MAIL_SSL_TLS=False,
    # MAIL_STARTTLS=True,
    #TEMPLATE_FOLDER=Path(__file__).parent.parent/"templates",
    TEMPLATE_FOLDER=Path(__file__).parent/"templates/"

)

async def send_token_email(subject:str, email_to:EmailStr, body, template:str):

    message = MessageSchema(
        subject=subject,
        recipients=[email_to,],
        template_body=body
    )
    
    fm = FastMail(config)
    try:
        await fm.send_message(message, template_name = template)
        return {
            "status": "success",
            "message": "Email sent successfully",
            "body": body
        }
    except ConnectionErrors as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Error sending email",
                "body": str(e)
            }
        )

