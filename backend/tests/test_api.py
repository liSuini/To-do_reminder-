# -*- coding: utf-8 -*-
"""API 路由层集成测试：穿过 HTTP 接缝验证端到端行为"""
import pytest
from fastapi.testclient import TestClient

from app.routers import make_app


@pytest.fixture
def client(session):
    app = make_app()
    return TestClient(app)


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_create_and_get_todo(client):
    r = client.post("/api/todos", json={"title": "API测试", "priority": "high"})
    assert r.status_code == 200
    todo_id = r.json()["id"]
    r2 = client.get(f"/api/todos/{todo_id}")
    assert r2.status_code == 200
    assert r2.json()["title"] == "API测试"


def test_create_validation_error(client):
    r = client.post("/api/todos", json={"title": ""})  # 空标题
    assert r.status_code == 422
    r2 = client.post("/api/todos", json={"title": "x", "priority": "顶级"})  # 非法枚举
    assert r2.status_code == 422


def test_view_query_excludes_no_due_date(client):
    client.post("/api/todos", json={"title": "无日期"})
    r = client.get("/api/todos", params={"view": "today"})
    assert r.status_code == 200
    assert r.json() == []


def test_update_todo(client):
    todo_id = client.post("/api/todos", json={"title": "旧"}).json()["id"]
    r = client.put(f"/api/todos/{todo_id}", json={"title": "新"})
    assert r.status_code == 200
    assert r.json()["title"] == "新"


def test_complete_toggle(client):
    todo_id = client.post("/api/todos", json={"title": "完成我"}).json()["id"]
    r = client.patch(f"/api/todos/{todo_id}/complete", json={"completed": True})
    assert r.status_code == 200
    assert r.json()["status"] == "completed"


def test_tags_endpoint(client):
    client.post("/api/todos", json={"title": "t", "tags": ["工作"]})
    assert "工作" in client.get("/api/tags").json()


def test_stats_endpoint(client):
    r = client.get("/api/stats", params={"view": "all"})
    assert r.json() == {"total": 0, "completed": 0, "overdue": 0}


def test_delete_and_404(client):
    todo_id = client.post("/api/todos", json={"title": "x"}).json()["id"]
    assert client.delete(f"/api/todos/{todo_id}").status_code == 200
    assert client.get(f"/api/todos/{todo_id}").status_code == 404
    assert client.delete(f"/api/todos/{todo_id}").status_code == 404
    assert client.put(f"/api/todos/{todo_id}", json={"title": "y"}).status_code == 404
    assert client.patch(f"/api/todos/{todo_id}/complete", json={"completed": True}).status_code == 404
