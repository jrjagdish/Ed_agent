from uuid import UUID

from pydantic import BaseModel,EmailStr

class UserResponse(BaseModel):
    id : UUID
    email : EmailStr
    token : str

class UserLogin(BaseModel):
    email : EmailStr
    password : str    

class UserCreate(BaseModel):
    username: str
    email : str
    password : str  
