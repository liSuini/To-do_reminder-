# -*- coding: utf-8 -*-
"""数据库引擎与会话工厂"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import DB_PATH

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


def init_db():
    """建表（幂等）"""
    from app import models  # noqa: F401 确保模型注册到 Base
    Base.metadata.create_all(engine)
