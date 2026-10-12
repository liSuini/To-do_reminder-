# -*- coding: utf-8 -*-
"""系统端点：健康检查（Electron 轮询就绪判断用）"""
from fastapi import APIRouter

router = APIRouter(prefix="/api")


@router.get("/health")
def health():
    return {"status": "ok"}
