# Hướng dẫn triển khai SSP Exam lên Internet (miễn phí)

Repo đã được chuẩn bị sẵn cho production:
- `requirements.txt` — danh sách package
- `vercel.json` + `wsgi.py` có biến `app` — cấu hình Vercel
- `settings.py` đọc cấu hình từ biến môi trường: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DATABASE_URL`, `CSRF_TRUSTED_ORIGINS`
- WhiteNoise phục vụ static files, `.gitignore` loại venv/db/media khỏi git

---

## So sánh 3 giải pháp miễn phí

| Tiêu chí | PythonAnywhere ⭐ | Render + Neon | Vercel + Neon |
|---|---|---|---|
| Kiểu chạy | Server truyền thống | Container | Serverless |
| Luôn online | ✅ | ⚠️ Ngủ sau 15 phút không truy cập (đánh thức ~50s) | ✅ (cold start ~1-3s) |
| Database miễn phí | ✅ SQLite/MySQL ngay trên máy | Neon Postgres 0.5GB | Neon Postgres 0.5GB |
| **Upload ảnh/avatar giữ được?** | ✅ Ổ đĩa thật | ❌ Mất khi redeploy | ❌ Mất ngay (serverless) |
| Tự deploy khi push GitHub | ❌ (kéo tay bằng git pull) | ✅ | ✅ |
| Địa chỉ miễn phí | `tenban.pythonanywhere.com` | `tenapp.onrender.com` | `tenapp.vercel.app` |
| Tên miền riêng (free tier) | ❌ | ✅ | ✅ |
| Phù hợp nhất | App Django đầy đủ tính năng, demo ổn định | Cân bằng | Push-to-deploy, chấp nhận hạn chế |

**Khuyến nghị:** dùng **PythonAnywhere** cho app này vì: luôn online, SQLite + upload ảnh câu hỏi/avatar hoạt động nguyên vẹn, không phải chuyển DB. Vercel phù hợp nếu bạn muốn quy trình push GitHub → tự deploy và chấp nhận 2 hạn chế: phải dùng Postgres ngoài (Neon) và ảnh upload không được lưu.

---

## PHƯƠNG ÁN A — Vercel + Neon Postgres (theo yêu cầu)

### Bước 0: Chuẩn bị tài khoản
- [github.com](https://github.com) — chứa code
- [vercel.com](https://vercel.com) — đăng nhập bằng GitHub (gói Hobby miễn phí)
- [neon.tech](https://neon.tech) — Postgres miễn phí 0.5GB (đăng nhập bằng GitHub)

### Bước 1: Tạo database trên Neon
1. Vào Neon → **New Project** → đặt tên `ssp-exam`, region **Singapore (ap-southeast-1)** cho gần Việt Nam.
2. Sau khi tạo, vào **Dashboard → Connection string**, chọn định dạng **psql/URL**, tick **Pooled connection**.
3. Copy chuỗi dạng:
   ```
   postgresql://user:password@ep-xxx-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
   ```

### Bước 2: Nạp dữ liệu vào Neon từ máy bạn
Mở PowerShell tại thư mục dự án:
```powershell
# Trỏ Django sang Neon (thay chuỗi kết nối của bạn)
$env:DATABASE_URL = "postgresql://user:password@ep-xxx-pooler...neon.tech/neondb?sslmode=require"

# Tạo bảng
.\venv\Scripts\python.exe manage.py migrate

# Tạo tài khoản quản trị
.\venv\Scripts\python.exe manage.py createsuperuser

# Nạp 100+ câu hỏi Python mẫu
.\venv\Scripts\python.exe manage.py seed_python_questions

# Xong thì xóa biến để local quay về SQLite
Remove-Item Env:DATABASE_URL
```

### Bước 3: Đẩy code lên GitHub
```powershell
# Bỏ theo dõi file không nên đưa lên (chỉ cần làm 1 lần)
git rm -r --cached db.sqlite3 2>$null
git rm -r --cached WebAppTestingSSP/__pycache__ accounts/__pycache__ 2>$null

git add -A
git commit -m "Chuan bi deploy production"
git push origin master
```

### Bước 4: Tạo project trên Vercel
1. Vercel → **Add New → Project** → **Import** repo `WebAppTestingSSP`.
2. Framework Preset: **Other**. KHÔNG cần Build Command/Output Directory (vercel.json lo hết).
3. Mở **Environment Variables**, thêm:

   | Name | Value |
   |---|---|
   | `DATABASE_URL` | chuỗi kết nối Neon ở Bước 1 |
   | `SECRET_KEY` | chuỗi ngẫu nhiên dài (chạy: `python -c "import secrets; print(secrets.token_urlsafe(50))"`) |
   | `DEBUG` | `False` |
   | `ALLOWED_HOSTS` | `.vercel.app` (thêm `,tenmien.com` nếu có tên miền) |

4. Bấm **Deploy**. Chờ 1-2 phút → nhận link `https://ten-app.vercel.app`.

### Bước 5: Kiểm tra
- Mở link → trang đăng nhập hiện ra → đăng nhập bằng tài khoản superuser tạo ở Bước 2.
- Từ nay **mỗi lần `git push` → Vercel tự deploy lại**.

### Hạn chế cần biết trên Vercel
1. **Upload ảnh không được lưu** (ảnh câu hỏi, avatar): filesystem serverless là tạm thời. Tránh dùng tính năng chèn ảnh, hoặc sau này tích hợp Cloudinary (có gói free).
2. **Request tối đa ~10 giây** (gói Hobby): các thao tác nặng như import file Excel hàng nghìn câu có thể bị cắt.
3. Muốn seed thêm dữ liệu → chạy lệnh từ máy bạn với `$env:DATABASE_URL` như Bước 2.

---

## PHƯƠNG ÁN B — PythonAnywhere (khuyến nghị, giữ nguyên mọi tính năng)

1. Đăng ký tài khoản **Beginner (free)** tại [pythonanywhere.com](https://www.pythonanywhere.com).
2. Mở **Consoles → Bash**, clone code:
   ```bash
   git clone https://github.com/khanh21062002/WebAppTestingSSP.git
   cd WebAppTestingSSP
   mkvirtualenv ssp --python=python3.12
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py seed_python_questions
   python manage.py collectstatic --noinput
   ```
3. Vào tab **Web → Add a new web app → Manual configuration → Python 3.12**.
4. Trong trang cấu hình web app:
   - **Virtualenv**: `/home/TENBAN/.virtualenvs/ssp`
   - **WSGI configuration file** (bấm vào link để sửa): xóa hết, dán:
     ```python
     import os, sys
     path = '/home/TENBAN/WebAppTestingSSP'
     if path not in sys.path:
         sys.path.insert(0, path)
     os.environ['DJANGO_SETTINGS_MODULE'] = 'WebAppTestingSSP.settings'
     os.environ['DEBUG'] = 'False'
     os.environ['SECRET_KEY'] = 'chuoi-ngau-nhien-cua-ban'
     os.environ['ALLOWED_HOSTS'] = 'TENBAN.pythonanywhere.com'
     from django.core.wsgi import get_wsgi_application
     application = get_wsgi_application()
     ```
   - **Static files**: URL `/static/` → Directory `/home/TENBAN/WebAppTestingSSP/staticfiles`;
     URL `/media/` → `/home/TENBAN/WebAppTestingSSP/media`
5. Bấm **Reload** → truy cập `https://TENBAN.pythonanywhere.com`.
6. Cập nhật code sau này: mở Bash → `cd WebAppTestingSSP && git pull && workon ssp && python manage.py migrate && python manage.py collectstatic --noinput` → bấm Reload.

Lưu ý free tier: web app cần bấm "Run until 3 months from today" gia hạn mỗi 3 tháng (1 click).

---

## Checklist bảo mật trước khi công khai
- [ ] `DEBUG=False` trên server (đã cấu hình qua env)
- [ ] `SECRET_KEY` mới, ngẫu nhiên, KHÔNG dùng key trong repo
- [ ] Đổi mật khẩu các tài khoản demo (admin/Admin@12345...)
- [ ] `ALLOWED_HOSTS` chỉ chứa domain thật
- [ ] Backup định kỳ: Neon có backup tự động; PythonAnywhere tải db.sqlite3 về máy
