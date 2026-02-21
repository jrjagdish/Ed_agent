from sqlalchemy import create_engine
from db.models import Base
from sqlalchemy.orm import sessionmaker
import os
from pydantic_settings import BaseSettings



class Settings(BaseSettings):
    DATABASE_URL: str
    
    class Config:
        env_file = ".env"

settings = Settings()
database_url =Settings.DATABASE_URL


engine = create_engine(
    database_url, echo=True
)
Base.metadata.create_all(bind=engine)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
