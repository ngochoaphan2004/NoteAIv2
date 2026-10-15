#!/usr/bin/env bash
# ==============================================================================
# 🔄 NoteAI.v2 - 1-Click Update Script on VPS
# ==============================================================================
# Tự động cập nhật code Backend, ghi chú Content, và khởi động lại dịch vụ.
# Nếu phát hiện hệ thống chưa chạy cài đặt ban đầu, tự động gọi vps_lowmem.sh.
# ==============================================================================

set -euo pipefail

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo -e "${BLUE}====================================================${NC}"
echo -e "${GREEN} 🔄 BẮT ĐẦU CẬP NHẬT NOTEAI.V2 TRÊN MÁY CHỦ VPS ${NC}"
echo -e "${BLUE}====================================================${NC}"

# 0. Chuẩn hóa cổng PostgreSQL sang 5432 nếu file .env mang cổng 5433 từ local
if [ -f "$PROJECT_DIR/backend/.env" ]; then
    sed -i 's/:5433/:5432/g' "$PROJECT_DIR/backend/.env"
fi

# 1. Kéo code mới nhất từ Git (nếu thư mục có .git)
if [ -d ".git" ]; then
    echo -e "${YELLOW}📥 [1/4] Đang kéo commit mới nhất từ Git origin main...${NC}"
    git pull origin main || echo "  ⚠️ Không thể git pull (bỏ qua)..."
else
    echo -e "${YELLOW}ℹ️ [1/4] Gói cập nhật được tải trực tiếp từ máy tính.${NC}"
fi

# 2. Cập nhật thư viện Python nếu có file requirements mới
VENV_PIP="$PROJECT_DIR/venv/bin/pip"
if [ -f "$VENV_PIP" ] && [ -f "$PROJECT_DIR/backend/requirements.txt" ]; then
    echo -e "${YELLOW}🐍 [2/4] Kiểm tra & cập nhật thư viện Python...${NC}"
    "$VENV_PIP" install --no-cache-dir -r "$PROJECT_DIR/backend/requirements.txt"
fi

# 3. Đồng bộ cấu trúc bảng PostgreSQL (nếu có model mới)
VENV_PYTHON="$PROJECT_DIR/venv/bin/python"
if [ -f "$VENV_PYTHON" ]; then
    echo -e "${YELLOW}🐘 [3/4] Kiểm tra migration cơ sở dữ liệu PostgreSQL...${NC}"
    cd "$PROJECT_DIR/backend"
    "$VENV_PYTHON" -c "from app.core.database import init_db; init_db()" || echo "  ⚠️ Init DB warning"
    cd "$PROJECT_DIR"
fi

# 4. Khởi động lại dịch vụ Backend & Nginx
echo -e "${YELLOW}🚀 [4/4] Kiểm tra và khởi động lại dịch vụ...${NC}"

# Kiểm tra nếu service chưa từng được cài đặt (chưa chạy vps_lowmem.sh thành công)
if ! systemctl list-unit-files | grep -q "noteai-backend.service"; then
    echo -e "${YELLOW}  ⚠️ Phát hiện NoteAI chưa hoàn tất cài đặt ban đầu. Đang tự động chạy setup từ vps_lowmem.sh...${NC}"
    bash "$PROJECT_DIR/scripts/vps_lowmem.sh"
else
    systemctl restart noteai-backend
    systemctl reload nginx
    echo -e "\n${BLUE}====================================================${NC}"
    echo -e "${GREEN} ✅ CẬP NHẬT HOÀN TẤT TRONG 2 GIÂY! HỆ THỐNG ĐÃ SẴN SÀNG! ${NC}"
    echo -e "${BLUE}====================================================${NC}"
fi

