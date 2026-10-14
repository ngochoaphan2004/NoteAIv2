FROM python:3.12-slim-bookworm

# Thiết lập môi trường
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    NODE_ENV=development \
    TZ=Asia/Ho_Chi_Minh

# Cài đặt các gói hệ thống cơ bản, Supervisor và Node.js 22 LTS
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    supervisor \
    ca-certificates \
    gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_22.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list \
    && apt-get update && apt-get install -y nodejs \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1. Cài đặt Python backend dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# 2. Cài đặt Quartz v4 root dependencies
COPY package.json package-lock.json* /app/
RUN npm install

# 3. Cài đặt Frontend React SPA dependencies
COPY frontend/package.json frontend/package-lock.json* /app/frontend/
RUN cd /app/frontend && npm install

# 4. Sao chép toàn bộ mã nguồn dự án
COPY . /app/

# 5. Tạo thư mục log cần thiết cho Supervisor và ứng dụng
RUN mkdir -p /app/logs/supervisor /app/backend/logs

# 6. Cấu hình Supervisor
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Mở các cổng dịch vụ (FastAPI: 8000, Vite: 5173, Quartz: 8088)
EXPOSE 8000 5173 8088

# Khởi chạy toàn bộ hệ thống qua Supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

