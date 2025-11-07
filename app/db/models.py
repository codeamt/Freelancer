from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user")
    created_at = Column(DateTime, server_default=func.now())

    media = relationship("Media", back_populates="user")

class Media(Base):
    __tablename__ = "media"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(String)
    url = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    uploaded_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="media")

class Product(Base):
    __tablename__ = "products"
    id = Column(String, primary_key=True)
    name = Column(String)
    price = Column(Float)
    currency = Column(String(3), default="USD")

class Course(Base):
    __tablename__ = "courses"
    id = Column(String, primary_key=True)
    title = Column(String)
    description = Column(String)

class Post(Base):
    __tablename__ = "posts"
    id = Column(String, primary_key=True)
    content = Column(Text)
    like_count = Column(Integer, default=0)