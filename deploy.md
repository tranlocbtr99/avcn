# Hướng dẫn deploy AVCN lên Render (mọi người trên máy họ truy cập được)

## Điều kiện
- Mã nguồn tại `/home/loctm/avcn-quiz`
- API key Render: `rnd_ZT9ayCmKjY5M3kylu13usuXb4Jvn` (dùng nếu bạn muốn điều khiển qua CLI/REST, không bắt buộc)
- Một tài khoản GitHub/GitLab (để push code lên, Render cần liên kết repo)

---

## Bước 1: Đẩy code lên GitHub

```bash
cd /home/loctm/avcn-quiz
git init
git add .
git commit -m "Init AVCN quiz app"
git remote add origin https://github.com/TEN-CUA-BAN/avcn-quiz.git
git push -u origin main
```

---

## Bước 2: Tạo Web Service trên Render

1. Truy cập https://render.com (đăng nhập).
2. Bấm **New +** → **Web Service**.
3. Kết nối với repo GitHub bạn vừa push (`avcn-quiz`).
4. Cấu hình:
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2`
   - **Instance type**: Free (hoặc Starter nếu cần ổ đĩa lớn hơn)

---

## Bước 3: Thiết lập biến môi trường

Trong trang quản trị dịch vụ Render, vào **Environment**, thêm:

| Key | Giá trị | Ghi chú |
|-----|---------|---------|
| `ADMIN_TOKEN` | `admin123` (hoặc thay bằng mã khác) | Token để vào trang báo cáo `/admin?token=...` |
| `SECRET_KEY` | bất kỳ chuỗi ngẫu nhiên | Khóa bảo mật Flask |
| `DB_PATH` | `/opt/render/project/data/results.db` | **Bắt buộc nếu tạo ổ đĩa bền (xem bước 4)** |

---

## Bước 4 (Quan trọng): Tạo ổ đĩa bền để lưu kết quả

Render miễn phí dùng ổ đĩa tạm → khi redeploy, file `results.db` (kết quả làm bài) sẽ bị xóa. Để dữ liệu người dùng không bị mất:

1. Trong dịch vụ Render, vào tab **Disks** → **Add Disk**:
   - **Name**: `avcn-data`
   - **Mount Path**: `/opt/render/project/data`
   - **Size**: 1 GB (ho lớn)
2. Lưu lại (dịch vụ sẽ khởi động lại).
3. Đảm bảo biến môi trường `DB_PATH` trỏ đúng: `/opt/render/project/data/results.db`

Kết quả: file `results.db` sẽ được lưu trên ổ đĩa bền, không bị mất khi restart/redeploy.

---

## Bước 5: Chia sẻ link cho mọi người

Render sẽ cấp một URL công khai, ví dụ:
```
https://avcn-quiz.onrender.com
```

- Người dùng truy cập link này → chọn đề → làm bài → nộp → xem kết quả.
- Bạn xem báo cáo tất cả người dùng: `https://avcn-quiz.onrender.com/admin?token=admin123`

---

## Cập nhật sau này

1. Sửa `vocab.json` (thêm/sửa từ vựng).
2. Chạy local: `python3 generate_questions.py` → sinh lại `questions.json`.
3. Commit và push lên GitHub. Render sẽ tự động redeploy.

---

## Lưu ý về gói miễn phí Render

- Gói free có thể "ngủ" sau một thời gian không có truy cập (lần truy cập đầu sẽ chậm vài giây).
- Nếu không tạo ổ đĩa bền (Bước 4), dữ liệu `results.db` sẽ mất khi Render rebuild dịch vụ. Nếu chỉ cần dùng thử ngắn hạn, có thể bỏ qua Bước 4, dữ liệu vẫn được lưu trong thời gian dịch vụ đang chạy.
