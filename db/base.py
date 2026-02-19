from sqlalchemy import create_engine
from db.models import Base
from sqlalchemy.orm import sessionmaker

engine = create_engine(
    "sqlite:///app.db", echo=True, connect_args={"check_same_thread": False}
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
