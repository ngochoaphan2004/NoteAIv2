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

# 4. Kiểm tra môi trường Node.js & dependencies của Quartz SSG
if [ -f "$PROJECT_DIR/package.json" ]; then
    if [ ! -d "$PROJECT_DIR/node_modules" ]; then
        echo -e "${YELLOW}📦 [4/5] node_modules chưa tồn tại. Đang cài đặt thư viện Quartz...${NC}"
        npm install --prefer-offline --no-audit || echo "  ⚠️ npm install warning"
    else
        echo -e "${YELLOW}📦 [4/5] Thư viện Quartz node_modules đã sẵn sàng.${NC}"
    fi
fi
if [ -d "$PROJECT_DIR/content/assets/audio" ]; then
    echo -e "${YELLOW}🎧 Liên kết audio tĩnh vào public/assets/audio...${NC}"
    mkdir -p "$PROJECT_DIR/public/assets"
    ln -sfn "$PROJECT_DIR/content/assets/audio" "$PROJECT_DIR/public/assets/audio"
fi

# 5. Khởi động lại dịch vụ Backend & Nginx
echo -e "${YELLOW}🚀 [5/5] Kiểm tra và khởi động lại dịch vụ...${NC}"

# Kiểm tra nếu service chưa từng được cài đặt (chưa chạy setup ban đầu)
if [ ! -f /etc/systemd/system/noteai-backend.service ]; then
    echo -e "${YELLOW}  ⚠️ Phát hiện NoteAI service chưa cài đặt. Vui lòng kiểm tra lại cấu hình systemd.${NC}"
else
    if [ -f "$PROJECT_DIR/scripts/noteai_nginx.conf" ]; then
        cp "$PROJECT_DIR/scripts/noteai_nginx.conf" /etc/nginx/sites-available/noteai
    fi
    systemctl daemon-reload
    systemctl restart noteai-backend
    nginx -t && systemctl reload nginx
    echo -e "\n${BLUE}====================================================${NC}"
    echo -e "${GREEN} ✅ CẬP NHẬT HOÀN TẤT! HỆ THỐNG ĐÃ SẴN SÀNG! ${NC}"
    echo -e "${BLUE}====================================================${NC}"
fi

