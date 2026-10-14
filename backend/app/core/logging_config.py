import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional
from datetime import datetime
from zoneinfo import ZoneInfo

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

# Định dạng chuẩn mực cho toàn bộ hệ thống
LOG_FORMAT = "%(asctime)s [%(levelname)s] [%(name)s:%(lineno)d]: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

class VietnamFormatter(logging.Formatter):
    """
    Formatter đảm bảo thời gian ghi log luôn luôn chuẩn theo Giờ Việt Nam (Asia/Ho_Chi_Minh - UTC+7),
    bất kể server/container Docker đang chạy ở múi giờ UTC hay tại datacenter nước ngoài.
    """
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=VN_TZ)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.strftime("%Y-%m-%d %H:%M:%S")

def get_log_dir() -> str:
    """Xác định thư mục logs an toàn cho cả môi trường local và Docker container"""
    # 1. Nếu biến môi trường LOG_DIR được chỉ định
    env_log_dir = os.getenv("LOG_DIR")
    if env_log_dir:
        os.makedirs(env_log_dir, exist_ok=True)
        return env_log_dir

    # 2. Mặc định trỏ về thư mục `logs/` ở thư mục gốc của project
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    log_dir = os.path.join(base_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir

def setup_logging(level: int = logging.INFO) -> str:
    """
    Khởi tạo hệ thống Ghi Log Bền Vững (Persistent Rotating Logger):
    1. Console Handler: Xuất ra stdout để theo dõi thời gian thực (docker logs -f).
    2. App Rotating Handler: Lưu toàn bộ sự kiện (INFO+) vào `logs/app.log` (tối đa 10MB/file, lưu 5 bản backup).
    3. Error Rotating Handler: Lưu riêng lỗi (WARNING, ERROR, CRITICAL) vào `logs/error.log`.
    """
    log_dir = get_log_dir()
    formatter = VietnamFormatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Xóa các handler mặc định cũ để tránh duplicate log
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # 1. Console Stream Handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 2. General App Log Handler (app.log - Max 10MB x 5 backups)
    app_log_path = os.path.join(log_dir, "app.log")
    app_file_handler = RotatingFileHandler(
        app_log_path,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    app_file_handler.setLevel(logging.INFO)
    app_file_handler.setFormatter(formatter)
    root_logger.addHandler(app_file_handler)

    # 3. Dedicated Error Log Handler (error.log - Max 10MB x 5 backups)
    error_log_path = os.path.join(log_dir, "error.log")
    error_file_handler = RotatingFileHandler(
        error_log_path,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    error_file_handler.setLevel(logging.WARNING)
    error_file_handler.setFormatter(formatter)
    root_logger.addHandler(error_file_handler)

    # Điều chỉnh mức log của các thư viện bên thứ 3 để tránh spam
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("watchfiles").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    root_logger.info(f"Persistent logging initialized successfully. Log directory: {log_dir}")
    return log_dir

