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

# 0. Chuẩn hóa cấu hình VPS: Khóa cổng nội bộ 127.0.0.1 (chỉ qua Cloudflare Tunnel)
if [ -f "$PROJECT_DIR/backend/.env" ]; then
    sed -i 's/:5433/:5432/g' "$PROJECT_DIR/backend/.env"
    sed -i 's/localhost:5432/127.0.0.1:5432/g' "$PROJECT_DIR/backend/.env"
    sed -i 's/HOST=0.0.0.0/HOST=127.0.0.1/g' "$PROJECT_DIR/backend/.env"
fi

# Tắt và vô hiệu hóa hoàn toàn Nginx (chặn đứng mọi truy cập trực tiếp qua IP public)
if systemctl is-active --quiet nginx || [ -f /etc/nginx/sites-enabled/noteai ]; then
    echo -e "${YELLOW}🛡️ Vô hiệu hóa Nginx để chuyển toàn bộ sang Cloudflare Tunnel...${NC}"
    systemctl stop nginx || true
    systemctl disable nginx || true
    rm -f /etc/nginx/sites-enabled/noteai || true
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

# 4. Kiểm tra môi trường Node.js & dependencies của Quartz SSG và Frontend
if [ -f "$PROJECT_DIR/package.json" ]; then
    if [ ! -d "$PROJECT_DIR/node_modules" ]; then
        echo -e "${YELLOW}📦 [4/5] node_modules chưa tồn tại. Đang cài đặt thư viện Quartz...${NC}"
        npm install --prefer-offline --no-audit || echo "  ⚠️ npm install warning"
    else
        echo -e "${YELLOW}📦 [4/5] Thư viện Quartz node_modules đã sẵn sàng.${NC}"
    fi
fi

# Đảm bảo frontend/dist sẵn sàng để FastAPI phục vụ trực tiếp
if [ ! -f "$PROJECT_DIR/frontend/dist/index.html" ] && [ -f "$PROJECT_DIR/frontend/package.json" ]; then
    echo -e "${YELLOW}⚛️ frontend/dist chưa được biên dịch. Tiến hành build React SPA...${NC}"
    cd "$PROJECT_DIR/frontend"
    npm install --prefer-offline --no-audit || true
    npm run build || true
    cd "$PROJECT_DIR"
fi

if [ -d "$PROJECT_DIR/content/assets/audio" ]; then
    echo -e "${YELLOW}🎧 Liên kết audio tĩnh vào public/assets/audio...${NC}"
    mkdir -p "$PROJECT_DIR/public/assets"
    ln -sfn "$PROJECT_DIR/content/assets/audio" "$PROJECT_DIR/public/assets/audio"
fi

# 5. Khởi động lại dịch vụ Backend (Định tuyến an toàn qua Cloudflare Tunnel)
echo -e "${YELLOW}🚀 [5/5] Cập nhật và khởi động lại dịch vụ...${NC}"

# Cập nhật hoặc cài đặt systemd service tự động nếu có tệp mẫu
if [ -f "$PROJECT_DIR/scripts/noteai-backend.service" ]; then
    cp "$PROJECT_DIR/scripts/noteai-backend.service" /etc/systemd/system/noteai-backend.service
    systemctl daemon-reload
    systemctl enable noteai-backend || true
fi

if systemctl is-active --quiet noteai-backend || [ -f /etc/systemd/system/noteai-backend.service ]; then
    systemctl restart noteai-backend
    echo -e "\n${BLUE}====================================================${NC}"
    echo -e "${GREEN} ✅ CẬP NHẬT HOÀN TẤT! HỆ THỐNG ĐÃ SẴN SÀNG CHO CLOUDFLARE TUNNEL! ${NC}"
    echo -e "${BLUE}====================================================${NC}"
else
    echo -e "${YELLOW}  ℹ️ NoteAI đang chạy trong Docker hoặc môi trường thủ công.${NC}"
fi

