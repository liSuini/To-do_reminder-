# -*- coding: utf-8 -*-
"""路由组装"""
from fastapi import FastAPI

from app.routers.system import router as system_router
from app.routers.todos import router as todos_router


def make_app() -> FastAPI:
    app = FastAPI(title="待办助手")
    app.include_router(todos_router)
    app.include_router(system_router)
    return app
