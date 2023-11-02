from pydantic import BaseModel, Field, EmailStr

# class OurBaseModel(BaseModel):
#     class Config:
#         orm_mode = True

class UserSchema(BaseModel):
    id: int = Field(default=None)
    first_name: str = Field(default=None)
    last_name: str = Field(default=None)
    email: EmailStr = Field(null=False, unique = True) 
    password: str = Field(default=None)
    confirm_password: str = Field(default=None)

    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "first_name": "John",
                "last_name": "Doe",
                "email": "johndoe@xyz.com",
                "password": "password",
                "confirm_password": "password"
            }
            }
        
class UserUpdateSchema(BaseModel):
    old_password: str = Field(default=None)
    new_password: str = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "old_password": "any",
                "new_password": "any"
            }
        }

class UserDeleteSchema(BaseModel):
    email: str = Field(default=None)
    password: str = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "email": "any@gmail.com",
                "password": "any"
            }
        }

class EmailSchema(BaseModel):
    email: EmailStr = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "email": "johndoe@xyz.com"
            }
        }