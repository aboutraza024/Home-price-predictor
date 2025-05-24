import uvicorn
from pydantic import BaseModel
from fastapi import FastAPI, Form, Depends, HTTPException, Request, BackgroundTasks, File, UploadFile
from sqlalchemy.orm import Session, sessionmaker, declarative_base
from sqlalchemy import create_engine, Integer, String, Column
import random

from starlette.middleware.sessions import SessionMiddleware

# SQLAlchemy Database Models


app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="Home_Price_Prediction")

SQL_ALCHEMY_DATABASE_URL = "mysql+pymysql://root:@localhost/home_price_predictor"
engine = create_engine(SQL_ALCHEMY_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Register_With_Email(Base):
    __tablename__ = "register_with_email"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True)
    first_name = Column(String(100), index=True)
    last_name = Column(String(100), index=True)
    password = Column(String(100), index=True)


class Register_With_Google(Base):
    __tablename__ = "register_with_google"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=False, index=True)


class Register_With_Github(Base):
    __tablename__ = "register_with_github"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)


Base.metadata.create_all(bind=engine)


# Pydantic models for user registration and login
class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str

    @classmethod
    def as_form(
            cls,
            first_name: str = Form(...),
            last_name: str = Form(...),
            email: str = Form(...),
            password: str = Form(...),
    ) -> "UserCreate":
        return cls(first_name=first_name, last_name=last_name, email=email, password=password)


class LoginUser(BaseModel):
    email: str
    password: str

    @classmethod
    def as_form(cls, email: str = Form(...), password: str = Form(...)) -> "LoginUser":
        return cls(email=email, password=password)


class PredictHouse(BaseModel):
    Purpose: str
    home: str
    Location: str
    Size: float
    Parking: int
    Bedrooms: int
    Washrooms: int
    Built_in_Year: int


    @classmethod
    def as_form(cls, Purpose: str = Form(...), home: str = Form(...),
                Location: str = Form(...), Size: float = Form(...), Parking: int = Form(...),
                Bedrooms: int = Form(...),
                Washrooms: int = Form(...), Built_in_Year: int = Form(...),
                ) -> "PredictHouse":
        return cls(Purpose=Purpose, home=home, Location=Location, Size=Size, Parking=Parking, Bedrooms=Bedrooms,
                   Washrooms=Washrooms, Built_in_Year=Built_in_Year)


# Database helper functions
def create_user(db: Session, email: str, first_name: str, last_name: str, password: str):
    db_user = Register_With_Email(email=email, first_name=first_name, last_name=last_name,
                                  password=password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_user_with_google(db: Session, email: str, user_name: str):
    db_user1 = Register_With_Google(email=email, username=user_name)
    db.add(db_user1)
    db.commit()
    db.refresh(db_user1)
    return db_user1


def create_user_with_github(db: Session, name: str, user_id: int):
    db_user2 = Register_With_Github(name=name, user_id=user_id)
    db.add(db_user2)
    db.commit()
    db.refresh(db_user2)
    return db_user2


def get_user_by_email_google(db: Session, email: str):
    return db.query(Register_With_Google).filter(Register_With_Google.email == email).first()


def get_user_by_github(db: Session, user_id):
    return db.query(Register_With_Github).filter(Register_With_Github.user_id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(Register_With_Email).filter(Register_With_Email.email == email).first()
