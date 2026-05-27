from sqlalchemy import create_engine, Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///fashion_metadata.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ItemMeta(Base):
    __tablename__ = "items"
    id = Column(String, primary_key=True, index=True)
    category = Column(String)       
    sub_category = Column(String)   
    color = Column(String)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True) 
    hashed_password = Column(String)
    reset_token = Column(String, nullable=True)    

class SavedOutfit(Base):
    __tablename__ = "saved_outfits"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    author_name = Column(String) 
    dominant_color = Column(String) 
    original_image_url = Column(String) 
    items_json = Column(String)        
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)