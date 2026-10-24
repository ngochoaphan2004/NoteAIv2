# 🌐 Hướng Dẫn Cấu Hình Cloudflare Tunnel (NoteAI.v2)

Tài liệu hướng dẫn kết nối hệ thống **NoteAI.v2** an toàn ra mạng Internet công cộng thông qua **Cloudflare Zero Trust Tunnel (`cloudflared`)** mà **KHÔNG CẦN NGINX** và **KHÔNG MỞ PORT TRỰC TIẾP RA IP PUBLIC**.

---

## 🛡️ 1. Tại Sao Tất Cả Port Đều Bị Khóa Trên `127.0.0.1`?

Trong `docker/docker-compose.yml`, toàn bộ các port đã được cấu hình gán cố định vào `127.0.0.1`:
- `127.0.0.1:5173` $\rightarrow$ React SPA Frontend
- `127.0.0.1:8000` $\rightarrow$ FastAPI Backend Gateway
- `127.0.0.1:8088` $\rightarrow$ Quartz v4 Digital Garden
- `127.0.0.1:5433` $\rightarrow$ PostgreSQL 16 (tránh xung đột với CVAT 5432)
- `127.0.0.1:6333` $\rightarrow$ Qdrant Vector DB

> **Lợi ích:** Bất kỳ ai cố tình quét IP VPS (ví dụ: `http://180.93.54.122:5173` hoặc `:8000`) đều sẽ bị kernel từ chối kết nối (*Connection Refused*). Chỉ có duy nhất tiến trình nội bộ `cloudflared` chạy trên máy mới có quyền đọc dữ liệu từ các cổng này.

---

## 🚀 2. Các Bước Cài Đặt Cloudflare Tunnel

### Bước 1: Cài đặt `cloudflared` trên VPS
```bash
# Ubuntu / Debian
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /etc/apt/trusted.gpg.d/cloudflare.gpg >/dev/null
echo "deb [signed-by=/etc/apt/trusted.gpg.d/cloudflare.gpg] https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/cloudflared.list
sudo apt update && sudo apt install -y cloudflared
```

### Bước 2: Đăng nhập & Tạo Tunnel
```bash
cloudflared tunnel login
cloudflared tunnel create noteai-tunnel
```
*Lưu lại UUID của Tunnel (ví dụ: `abc12345-6789-...`)*

### Bước 3: Cấu hình Ingress Rules (`/etc/cloudflared/config.yml`)
Tạo tệp `/etc/cloudflared/config.yml` với nội dung mẫu:

```yaml
tunnel: <UUID_CỦA_TUNNEL>
credentials-file: /root/.cloudflared/<UUID_CỦA_TUNNEL>.json

ingress:
  # 1. Tên miền truy cập NoteAI.v2 (Phục vụ trọn gói React SPA, Login Guard & Backend API trên port 8000)
  - hostname: ielts.yourdomain.com
    service: http://127.0.0.1:8000

  # 2. Tên miền truy cập Quartz Digital Garden độc lập (nếu chạy preview 8088 hoặc truy cập qua ielts.yourdomain.com/garden)
  - hostname: garden.yourdomain.com
    service: http://127.0.0.1:8000/garden

  # 3. Catch-all mặc định (bắt buộc)
  - service: http_status:404
```

> 💡 **Lưu ý quan trọng về Quick Tunnel (Thử nghiệm nhanh không cần domain):**
> Lệnh chạy Quick Tunnel chính xác:
> ```bash
> cloudflared tunnel --url http://127.0.0.1:8000 --protocol http2 --no-autoupdate
> ```
> *(Trỏ về `http://127.0.0.1:8000`, KHÔNG trỏ về port 5173 vì trên VPS không chạy Vite dev server)*

### Bước 4: Trỏ DNS CNAME trong Cloudflare
```bash
cloudflared tunnel route dns noteai-tunnel ielts.yourdomain.com
cloudflared tunnel route dns noteai-tunnel garden.yourdomain.com
```

### Bước 5: Kích hoạt Service chạy nền tự động
```bash
sudo cloudflared service install
sudo systemctl enable --now cloudflared
```

---

## 🔐 3. Tài Khoản Đăng Nhập Mặc Định

Khi người dùng mở URL `https://ielts.yourdomain.com`:
- Hệ thống sẽ hiển thị giao diện **Đăng Nhập NoteAI.v2**
- **Tài khoản mặc định:**
  - **Tên đăng nhập:** `admin`
  - **Mật khẩu:** `noteai2026`
- Có thể đổi mật khẩu và secret key trong `backend/.env`:
  ```ini
  AUTH_USERNAME=your_username
  AUTH_PASSWORD=your_strong_password
  AUTH_SECRET_KEY=your_custom_secret_key_random
  ```
