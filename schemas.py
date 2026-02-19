from pydantic import BaseModel,EmailStr

class UserResponse(BaseModel):
    id : int
    username : str
    email : EmailStr
    token : str

class UserLogin(BaseModel):
    email : EmailStr
    password : str    

class UserCreate(BaseModel):
    username: str
    email : str
    password : str  
