# -*- coding: utf-8 -*-
"""runner 组装根测试：端口探测可用 + create_app 组装完整"""
import socket

from fastapi.testclient import TestClient


def test_find_free_port_returns_usable():
    from app.runner import find_free_port
    port = find_free_port(8000)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", port))  # 能绑定说明确实可用


def test_find_free_port_skips_occupied():
    from app.runner import find_free_port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as blocker:
        blocker.bind(("127.0.0.1", 8000))
        blocker.listen(1)
        port = find_free_port(8000)
        assert port != 8000  # 被占则递增


def test_create_app_health_without_scheduler(session):
    """start_scheduler=False 时（TestClient 场景）health 依然可达"""
    from app.runner import create_app
    client = TestClient(create_app(start_scheduler=False))
    assert client.get("/api/health").status_code == 200
