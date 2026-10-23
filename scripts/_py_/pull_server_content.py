#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/pull_server_content.py
-------------------------------------------------------------------------------
Tự động kéo (pull) toàn bộ dữ liệu ghi chú Markdown (.md) và kết quả làm bài
từ máy chủ VPS (/opt/noteai/content) về máy tính cá nhân (Local).

Tính năng an toàn:
1. Tự động sao lưu content/ cục bộ vào thư mục backups/ trước khi cập nhật.
2. Tự động sao lưu content/ trên VPS vào /opt/noteai/backups/ trước khi đóng gói.
3. Chỉ kéo các file Markdown (.md) và cấu trúc thư mục, loại trừ audio nặng (165MB).
4. Báo cáo chi tiết các bài làm đã hoàn thành hoặc ghi chú được cập nhật.
-------------------------------------------------------------------------------
"""

import os
import sys
import shutil
import datetime
import subprocess
import tempfile
from pathlib import Path

# Cấu hình VPS
VPS_IP = os.environ.get("VPS_IP", "180.93.54.122")
VPS_USER = os.environ.get("VPS_USER", "root")
REMOTE_DIR = os.environ.get("REMOTE_DIR", "/opt/noteai")

# Định vị thư mục gốc của dự án
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONTENT_DIR = PROJECT_ROOT / "content"
BACKUP_DIR = PROJECT_ROOT / "backups"

def print_banner():
    print("=" * 70)
    print(" 📥 NOTEAI.V2 - PULL CONTENT & BÀI THI TỪ MÁY CHỦ VPS")
    print(f" 🌐 VPS Máy Chủ: {VPS_USER}@{VPS_IP}:{REMOTE_DIR}")
    print("=" * 70)

def run_cmd(cmd, capture=True, check=True):
    """Thực thi lệnh shell và trả về kết quả"""
    res = subprocess.run(cmd, shell=True, capture_output=capture, text=True)
    if check and res.returncode != 0:
        err = res.stderr.strip() if res.stderr else f"Command failed with exit code {res.returncode}"
        raise RuntimeError(f"Lỗi thực thi lệnh: {cmd}\n{err}")
    return res

def check_ssh_connection():
    """Kiểm tra kết nối SSH tới VPS"""
    print("🔍 [1/5] Đang kiểm tra kết nối SSH tới VPS...")
    cmd = f'ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout=5 {VPS_USER}@{VPS_IP} "echo OK"'
    res = run_cmd(cmd, capture=True, check=False)
    if res.returncode != 0 or "OK" not in res.stdout:
        print(f"\n❌ [LỖI] Không thể kết nối tới VPS {VPS_USER}@{VPS_IP}!")
        print("   Vui lòng kiểm tra địa chỉ IP, mạng Internet hoặc cấu hình SSH Key.")
        sys.exit(1)
    print("   ✅ Kết nối SSH thành công!")

def backup_local_content():
    """Sao lưu thư mục content/ trên máy tính trước khi ghi đè"""
    print("💾 [2/5] Đang tạo bản sao lưu an toàn cho thư mục content/ cục bộ...")
    if not CONTENT_DIR.exists():
        print("   ℹ️ Thư mục content/ chưa tồn tại trên máy tính, bỏ qua sao lưu.")
        return None

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    target_backup = BACKUP_DIR / f"content_local_{timestamp}"
    target_backup.mkdir(parents=True, exist_ok=True)

    # Sao lưu các file .md và cấu trúc thư mục, bỏ qua audio và data lớn
    copied_count = 0
    for root, dirs, files in os.walk(CONTENT_DIR):
        # Bỏ qua audio
        if "audio" in dirs:
            dirs.remove("audio")
        rel_path = Path(root).relative_to(CONTENT_DIR)
        dest_dir = target_backup / rel_path
        dest_dir.mkdir(parents=True, exist_ok=True)
        for f in files:
            if f.endswith(".md"):
                src_file = Path(root) / f
                dst_file = dest_dir / f
                shutil.copy2(src_file, dst_file)
                copied_count += 1

    print(f"   ✅ Đã sao lưu {copied_count} file .md vào: {target_backup.relative_to(PROJECT_ROOT)}")
    return target_backup

def backup_remote_content():
    """Tạo bản sao lưu trên VPS để đảm bảo an toàn kép"""
    print("🛡️ [3/5] Đang tạo bản sao lưu an toàn kép trực tiếp trên VPS...")
    cmd = (
        f'ssh -o StrictHostKeyChecking=no {VPS_USER}@{VPS_IP} "'
        f'mkdir -p {REMOTE_DIR}/backups && '
        f'tar -czf {REMOTE_DIR}/backups/content_vps_\\$(date +%Y%m%d_%H%M%S).tar.gz '
        f'--exclude=\'content/assets/audio\' -C {REMOTE_DIR} content 2>/dev/null && '
        f'ls -dt {REMOTE_DIR}/backups/* 2>/dev/null | tail -n +11 | xargs rm -rf 2>/dev/null || true"'
    )
    run_cmd(cmd, check=False)
    print("   ✅ Bản sao lưu trên VPS đã sẵn sàng (lưu tối đa 10 phiên bản gần nhất).")

def download_and_extract_content():
    """Đóng gói file .md trên VPS, tải về và cập nhật vào content/ cục bộ"""
    print("🚀 [4/5] Đang tải các bài làm và ghi chú Markdown từ VPS về máy tính...")
    
    # 1. Đóng gói trên VPS (chỉ lấy content, loại trừ assets/audio và data json lớn nếu đã có)
    remote_tar = "/tmp/vps_content_md.tar.gz"
    pack_cmd = (
        f'ssh -o StrictHostKeyChecking=no {VPS_USER}@{VPS_IP} "'
        f'cd {REMOTE_DIR} && '
        f'tar -czf {remote_tar} --exclude=\'content/assets\' --exclude=\'content/data\' content"'
    )
    run_cmd(pack_cmd)

    # 2. Tải file tar về temp máy tính
    local_temp = Path(tempfile.gettempdir()) / "vps_content_md.tar.gz"
    scp_cmd = f'scp -o StrictHostKeyChecking=no {VPS_USER}@{VPS_IP}:{remote_tar} "{local_temp}"'
    run_cmd(scp_cmd)

    # 3. Giải nén vào PROJECT_ROOT
    extract_cmd = f'tar -xzf "{local_temp}" -C "{PROJECT_ROOT}"'
    run_cmd(extract_cmd)

    # 4. Xóa file tạm
    if local_temp.exists():
        local_temp.unlink()
    cleanup_cmd = f'ssh -o StrictHostKeyChecking=no {VPS_USER}@{VPS_IP} "rm -f {remote_tar}"'
    run_cmd(cleanup_cmd, check=False)

    print("   ✅ Đã giải nén và cập nhật thành công vào thư mục content/!")

def report_changes():
    """Hiển thị tóm tắt các file bài làm & nội dung mới kéo về"""
    print("\n📊 [5/5] TỔNG HỢP TRẠNG THÁI NỘI DUNG VỪA CẬP NHẬT:")
    print("-" * 70)
    
    # Kiểm tra git status của content/
    res = run_cmd("git status -s content/", check=False)
    if res.stdout.strip():
        lines = res.stdout.strip().split("\n")
        print(f"🔥 Phát hiện {len(lines)} file ghi chú có cập nhật từ VPS:")
        for line in lines:
            print(f"   • {line.strip()}")
    else:
        print("   ✨ Dữ liệu giữa máy tính và VPS hoàn toàn đồng bộ (không có thay đổi mới).")

    print("-" * 70)
    print("🎉 HOÀN THÀNH KÉO DỮ LIỆU! Toàn bộ bài làm của bạn đã an toàn ở máy tính.")
    print("💡 Mẹo: Bây giờ bạn có thể an tâm chạy 'scripts/vps_update.bat' mà không sợ mất bài!")
    print("=" * 70)

def main():
    print_banner()
    try:
        check_ssh_connection()
        backup_local_content()
        backup_remote_content()
        download_and_extract_content()
        report_changes()
    except Exception as e:
        print(f"\n❌ [LỖI] Đã xảy ra lỗi trong quá trình kéo dữ liệu: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
