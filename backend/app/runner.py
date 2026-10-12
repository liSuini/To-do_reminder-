# -*- coding: utf-8 -*-
"""runner — 组装根：唯一知道"一切如何拼起来"的地方。

职责：
- create_app：数据库初始化 + 路由挂载 + 启动补发 + APScheduler 调度 + 静态托管
- find_free_port：端口探测（8000 被占自动递增）
- main：写 backend.port 文件（Electron 发现端口的约定）+ 启动 uvicorn
"""
import logging
import socket
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import DEFAULT_PORT, FRONTEND_DIST, PORT_FILE, SCAN_INTERVAL_SECONDS
from app.database import init_db
from app.notify.winotify_notifier import WinotifyNotifier
from app.routers import make_app
from app.services import todo_service
from app.services.reminder_engine import ReminderEngine

logger = logging.getLogger(__name__)


def find_free_port(start: int = DEFAULT_PORT) -> int:
    for port in range(start, start + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("50 个端口内无可用端口")


def create_app(start_scheduler: bool = True) -> FastAPI:
    init_db()
    app = make_app()

    engine = ReminderEngine(
        service=todo_service,
        notifier=WinotifyNotifier(),
        now=datetime.now,
    )
    engine.backfill_missed()  # 启动补发错过的提醒（CONTEXT.md 规则）

    if start_scheduler:
        from apscheduler.schedulers.background import BackgroundScheduler

        scheduler = BackgroundScheduler()
        scheduler.add_job(
            engine.scan_and_fire, "interval",
            seconds=SCAN_INTERVAL_SECONDS, max_instances=1,
        )
        scheduler.start()
        app.state.scheduler = scheduler

    if FRONTEND_DIST.exists():
        app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="static")
        logger.info("静态前端已挂载: %s", FRONTEND_DIST)
    return app


def main():
    logging.basicConfig(level=logging.INFO)
    port = find_free_port(DEFAULT_PORT)
    PORT_FILE.write_text(str(port), encoding="utf-8")
    print(f"BACKEND_READY port={port}", flush=True)

    import uvicorn

    uvicorn.run(create_app(), host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    main()
