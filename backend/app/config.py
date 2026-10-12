# -*- coding: utf-8 -*-
"""应用配置"""
import os
import sys
from pathlib import Path


def _base_dir() -> Path:
    """打包后（PyInstaller frozen）可写运行文件落在 exe 同目录；开发态落在 backend/"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def _data_dir() -> Path:
    """数据目录：frozen 时用 %APPDATA%（portable 模式 TEMP 目录退出即删，DB 必须持久化）"""
    if getattr(sys, "frozen", False):
        appdata = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        d = Path(appdata) / "TodoReminder"
        d.mkdir(parents=True, exist_ok=True)
        return d
    return Path(__file__).resolve().parent.parent


BACKEND_DIR = _base_dir()

DB_PATH = _data_dir() / "todo.db"
DEFAULT_PORT = 8000
SCAN_INTERVAL_SECONDS = 30
PORT_FILE = BACKEND_DIR / "backend.port"
FRONTEND_DIST = BACKEND_DIR / "frontend_dist"
