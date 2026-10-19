# TutorSim – Web (HTML/CSS/JS thuần)

Giao diện theo Figma "TutorSim UI v1" (Light/Dark), gọi trực tiếp backend TutorSim v1.7.
Không cần cài đặt hay build: chỉ là file tĩnh.

## Cấu trúc
```
index.html            trang duy nhất (app dùng hash: #/login, #/t/home, #/s/home, #/m/overview…)
config.js             >>> SỬA API_URL Ở ĐÂY khi deploy <<<
assets/styles.css     màu, chữ, bố cục theo Figma (biến CSS cho sáng/tối)
assets/js/api.js      mọi lời gọi backend
assets/js/app.js      điều hướng, khung theo vai, menu tài khoản, công tắc sáng/tối
assets/js/views/      auth.js · student.js · tutor.js · manager.js
assets/img/           hình minh họa, icon xuất từ Figma
```

## Chạy thử trên máy
1. Chạy backend: `cd backend && uvicorn app.main:app --reload` (cổng 8000).
2. Mở web: `cd web && python -m http.server 5173` rồi vào http://localhost:5173
   (để trống `API_URL` thì web tự gọi http://localhost:8000).
   Tài khoản thử (SEED_DEMO=1): gia sư `minh`, học sinh `ha`, mật khẩu `demo1234`; quản lý `quanly` / MANAGER_PASSWORD.

## Deploy
1. Sửa `config.js`: `API_URL: "https://<địa-chỉ-backend>"` (không có "/" cuối).
2. Ở backend, thêm địa chỉ web vào `CORS_ORIGINS` (ví dụ `https://tutorsim.vercel.app`) rồi khởi động lại.
3. Đưa cả thư mục `web/` lên bất kỳ hosting tĩnh nào:
   - **Vercel**: New Project → chọn repo → Root Directory `web` → Framework "Other" → Deploy (không cần build command).
   - **Netlify**: kéo thả thư mục `web` vào app.netlify.com/drop.
   - **GitHub Pages**: đẩy nội dung `web/` lên nhánh `gh-pages` hoặc thư mục `docs/`.
   App dùng đường dẫn dạng `#/...` nên không cần cấu hình rewrite.

## Ghi chú
- Đồ thị dùng GeoGebra (tải từ geogebra.org khi cần).
- Chế độ sáng/tối lưu theo từng trình duyệt (nút ở góc dưới phải).
- Token đăng nhập lưu trong localStorage của trình duyệt; hết hạn thì tự về màn đăng nhập.
