// =====================================================================
//  CẤU HÌNH TRIỂN KHAI – chỉ cần sửa dòng API_URL bên dưới khi deploy.
//  API_URL = địa chỉ backend TutorSim (FastAPI), KHÔNG có dấu "/" ở cuối.
//    Ví dụ: "https://tutorsim-api.onrender.com"
//  Để trống ("") thì tự dùng http://localhost:8000 khi chạy trên máy.
//  Nhớ thêm địa chỉ web này vào CORS_ORIGINS trong backend/.env.
// =====================================================================
window.TUTORSIM_CONFIG = {
  API_URL: "https://apigdglive.deeplunaria.page",
};
