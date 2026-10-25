#!/usr/bin/env bash
# ==============================================================================
# 🧹 NoteAI.v2 - Clean Server Script (/opt/noteai/clean_content.sh)
# ==============================================================================
# Xóa hoàn toàn các file trên server từ content, dist, logs, script...
# TUYỆT ĐỐI GIỮ LẠI (DEPENDENCIES & CRITICAL SECRETS):
#   - venv/ (Python Virtualenv & tất cả AI packages)
#   - backend/.env (Database credentials & Gemini API Key)
#   - scripts/ (Thư mục công cụ bảo trì server)
# (Đã XÓA HOÀN TOÀN: content/, audio/, dist/, code cũ)
# ==============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

PROJECT_DIR="/opt/noteai"
cd "$PROJECT_DIR"

echo -e "${BLUE}====================================================================${NC}"
echo -e "${GREEN} 🧹 NOTEAI.V2 - CLEAN SERVER TOOL (/opt/noteai) ${NC}"
echo -e "${BLUE}====================================================================${NC}"

# Chế độ chạy: 1 = Content, Dist & Audio, 2 = Full Reset (trừ dependencies)
MODE="${1:-}"

if [ -z "$MODE" ]; then
    echo -e "${YELLOW}Vui lòng chọn chế độ dọn dẹp server:${NC}"
    echo -e "  ${CYAN}[1] Dọn sạch Content, Audio & Dist/Build cũ${NC}"
    echo -e "      👉 Xóa: content (gồm cả audio), dist, script cũ, logs"
    echo -e "      👉 Giữ lại: backend, frontend, venv, .env"
    echo -e "  ${CYAN}[2] Dọn sạch TOÀN BỘ Server (Full Reset trừ dependencies)${NC}"
    echo -e "      👉 Xóa: content (gồm cả audio), dist, script, backend, frontend, templates"
    echo -e "      👉 Giữ lại: venv, .env, scripts"
    echo -e "  ${RED}[0] Hủy bỏ${NC}"
    echo ""
    read -p "Nhập lựa chọn của bạn (1, 2 hoặc 0): " choice
    MODE="$choice"
fi

if [ "$MODE" == "0" ] || [ "$MODE" == "cancel" ]; then
    echo -e "${YELLOW}Đã hủy thao tác dọn dẹp.${NC}"
    exit 0
fi

# ==============================================================================
# BƯỚC 1: BẢO TỒN BIẾN MÔI TRƯỜNG QUAN TRỌNG (BACKEND/.ENV)
# ==============================================================================
echo -e "\n${YELLOW}🛡️ [1/3] Đang bảo lưu tệp cấu hình quan trọng (backend/.env)...${NC}"
PRESERVE_DIR="/tmp/noteai_preserve_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$PRESERVE_DIR"

# Lưu backend/.env nếu có
if [ -f "$PROJECT_DIR/backend/.env" ]; then
    cp -p "$PROJECT_DIR/backend/.env" "$PRESERVE_DIR/backend.env"
    echo -e "   ✅ Đã bảo lưu: backend/.env"
fi

# ==============================================================================
# BƯỚC 2: THỰC HIỆN XÓA THEO CHẾ ĐỘ ĐÃ CHỌN
# ==============================================================================
echo -e "\n${YELLOW}🗑️ [2/3] Đang thực hiện dọn dẹp các tệp tin theo yêu cầu...${NC}"

# Dọn các thư mục rác / build cũ luôn luôn cần xóa
rm -rf "$PROJECT_DIR/dist" 2>/dev/null || true
echo -e "   • Đã xóa: dist/ (thư mục build rác cũ)"

rm -rf "$PROJECT_DIR/script" 2>/dev/null || true
echo -e "   • Đã xóa: script/ (thư mục cũ thừa dạng số ít)"

rm -rf "$PROJECT_DIR/public" 2>/dev/null || true
echo -e "   • Đã xóa: public/ (thư mục Quartz static build cũ)"

rm -rf "$PROJECT_DIR/frontend/dist" 2>/dev/null || true
echo -e "   • Đã xóa: frontend/dist/ (thư mục Frontend SPA build cũ)"

# Dọn logs
if [ -d "$PROJECT_DIR/logs" ]; then
    find "$PROJECT_DIR/logs" -type f -name "*.log*" -delete 2>/dev/null || true
    echo -e "   • Đã làm sạch: logs/"
fi

# Xóa file tạm
rm -f /tmp/noteai_*.tar.gz /tmp/vps_*.tar.gz 2>/dev/null || true

# Xóa content hoàn toàn (bao gồm cả audio)
rm -rf "$PROJECT_DIR/content" 2>/dev/null || true
echo -e "   • Đã xóa hoàn toàn: content/ (bao gồm toàn bộ audio, bài thi, tài liệu)"

if [ "$MODE" == "2" ] || [ "$MODE" == "all" ] || [ "$MODE" == "full" ]; then
    echo -e "\n${RED}⚠️ Đang thực hiện Full Clean Reset (Xóa toàn bộ mã nguồn cũ)...${NC}"
    systemctl stop noteai-backend 2>/dev/null || true

    rm -rf "$PROJECT_DIR/backend" 2>/dev/null || true
    echo -e "   • Đã xóa: backend/"

    rm -rf "$PROJECT_DIR/frontend" 2>/dev/null || true
    echo -e "   • Đã xóa: frontend/"

    rm -rf "$PROJECT_DIR/templates" 2>/dev/null || true
    echo -e "   • Đã xóa: templates/"
fi

# ==============================================================================
# BƯỚC 3: PHỤC HỒI BIẾN MÔI TRƯỜNG & KIỂM TRA TRẠNG THÁI
# ==============================================================================
echo -e "\n${YELLOW}✨ [3/3] Đang thiết lập lại cấu trúc sạch cho server...${NC}"

# Khôi phục backend/.env
if [ -f "$PRESERVE_DIR/backend.env" ]; then
    mkdir -p "$PROJECT_DIR/backend"
    cp -p "$PRESERVE_DIR/backend.env" "$PROJECT_DIR/backend/.env"
    echo -e "   ✅ Đã khôi phục: backend/.env"
fi

# Dọn dẹp thư mục tạm
rm -rf "$PRESERVE_DIR" 2>/dev/null || true

echo -e "\n${BLUE}====================================================================${NC}"
echo -e "${GREEN} 🎉 DỌN DẸP HOÀN TẤT! CÂY THƯ MỤC HIỆN TẠI TRÊN SERVER: ${NC}"
echo -e "${BLUE}====================================================================${NC}"
ls -la "$PROJECT_DIR"

echo -e "\n${CYAN}💡 BƯỚC TIẾP THEO:${NC}"
if [ "$MODE" == "2" ] || [ "$MODE" == "all" ] || [ "$MODE" == "full" ]; then
    echo -e "  Server đã sẵn sàng ở trạng thái sạch 100% (Dependencies & venv còn nguyên)."
    echo -e "  Hãy chạy ${YELLOW}vps_update.bat${NC} từ máy tính của bạn để tải bản cập nhật mới nhất lên!"
else
    echo -e "  Content và build cũ đã được xóa sạch."
    echo -e "  Hãy chạy ${YELLOW}vps_update.bat${NC} từ máy tính để cập nhật nội dung mới!"
fi
echo -e "${BLUE}====================================================================${NC}"
