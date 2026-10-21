# AVCN - Bộ đề thi trắc nghiệm online (tiếng Anh tài chính - ngân hàng)

Chạy được thực sự, lưu kết quả trên máy của bạn.

## Cấu trúc
- `vocab.json` — 531 thuật ngữ (nguồn sự thật, trích từ `AVCN all.docx`)
- `questions.json` — 10 đề × 60 câu, sinh tự động từ `vocab.json`
- `generate_questions.py` — script sinh câu hỏi (chạy lại khi cập nhật từ vựng)
- `app.py` — Flask backend (1 file)
- `templates/` — giao diện: trang chủ, làm bài, kết quả, báo cáo admin
- `static/style.css`, `static/app.js` — giao diện + hẹn giờ 90 phút
- `results.db` — CSDL SQLite lưu kết quả tất cả người dùng (trên máy bạn)

## Yêu cầu chính (đã đáp)
- 10 bộ đề, mỗi bộ 60 câu trắc nghiệm, toàn bộ 531 từ vựng được bao quát
- Giới hạn làm bài 90 phút (đếm ngược, nộp tự động khi hết giờ)
- Xem kết quả ngay sau khi nộp bài (điểm, câu đúng/sai, giải thích)
- Đáp án A/B/C/D phân bổ đều: mỗi đề đúng 15 câu mỗi đáp án
- Mức độ cao: nhận biết từ, đầu nghĩa, định nghĩa tiếng Anh, hiểu ngữ cảnh
- Không tạo câu ngoài kho từ vựng đã cung cấp
- Dễ cập nhật: sửa `vocab.json` rồi chạy `generate_questions.py`
- Báo cáo kết quả của **các người dùng khác về máy của bạn** (trang `/admin`)

## Chạy local (khuyên dùng — kết quả nằm trên máy bạn)
```
cd /home/loctm/avcn-quiz
pip install -r requirements.txt
python3 app.py
```
Truy cập: http://127.0.0.1:5000

Kết quả làm bài được lưu trong `results.db` trên máy của bạn. Xem báo cáo tất cả người dùng:
http://127.0.0.1:5000/admin?token=admin123

## Triển khai trên Render (dùng API key bạn cung cấp)
1. Đẩy mã này lên một kho Git (GitHub/GitLab).
2. Trên Render tạo Web Service, chọn repo, môi trường Python.
3. Hoặc dùng Render API key `rnd_ZT9ayCmKjY5M3kylu13usuXb4Jvn` qua `render-cli`/REST API để tạo service từ `render.yaml`.
4. Biến môi trường: `ADMIN_TOKEN` (mặc định `admin123`), `SECRET_KEY`, `PORT`.

Lưu ý: gói miễn phí Render có ổ đĩa tạm — dữ liệu `results.db` sẽ mất khi redeploy. Nếu muốn lưu kết quả vĩnh viễn trên máy của bạn, hãy chạy local (xem ở trên) hoặc gắn ổ đĩa bền.Render (sticky disk) / dùng CSDL riêng.

## Cập nhật từ vựng sau này
1. Sửa/thêm từ trong `vocab.json` (mỗi mục: term, def_en, mean_vi).
2. `python3 generate_questions.py` → sinh lại `questions.json` (10 × 60 câu, cân bằng đáp án).
3. Khởi động lại `app.py`.

## Mặc định
- Token quản trị: `admin123` (thay đổi trong `app.py` hoặc biến môi trường `ADMIN_TOKEN`)
- Thời gian làm bài: 90 phút (`TEST_TIME_SEC` trong `app.py`)
