# -*- coding: utf-8 -*-
"""应用配置"""
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent

DB_PATH = BACKEND_DIR / "todo.db"
DEFAULT_PORT = 8000
SCAN_INTERVAL_SECONDS = 30
PORT_FILE = BACKEND_DIR / "backend.port"
FRONTEND_DIST = BACKEND_DIR / "frontend_dist"
