# -*- coding: utf-8 -*-
"""HTTP 路由层：刻意做薄，业务规则全在 todo_service（一处修复全局生效）"""
from fastapi import APIRouter, HTTPException

from app.schemas import TodoCreate, TodoUpdate
from app.services import todo_service

router = APIRouter(prefix="/api")


@router.post("/todos")
def create_todo(payload: TodoCreate):
    return todo_service.create_todo(payload.model_dump())


@router.get("/todos")
def list_todos(view: str = "all", tag: str | None = None,
               priority: str | None = None, status: str | None = None):
    return todo_service.query_todos(view=view, tag=tag, priority=priority, status=status)


@router.get("/todos/{todo_id}")
def get_todo(todo_id: int):
    result = todo_service.get_todo(todo_id)
    if result is None:
        raise HTTPException(status_code=404, detail="待办不存在")
    return result


@router.put("/todos/{todo_id}")
def update_todo(todo_id: int, payload: TodoUpdate):
    result = todo_service.update_todo(todo_id, payload.model_dump())
    if result is None:
        raise HTTPException(status_code=404, detail="待办不存在")
    return result


@router.delete("/todos/{todo_id}")
def delete_todo(todo_id: int):
    if not todo_service.delete_todo(todo_id):
        raise HTTPException(status_code=404, detail="待办不存在")
    return {"ok": True}


@router.patch("/todos/{todo_id}/complete")
def complete_todo(todo_id: int, body: dict):
    result = todo_service.set_completed(todo_id, bool(body.get("completed", True)))
    if result is None:
        raise HTTPException(status_code=404, detail="待办不存在")
    return result


@router.get("/tags")
def tags():
    return todo_service.get_tag_names()


@router.get("/stats")
def stats(view: str = "all"):
    return todo_service.get_stats(view=view)
