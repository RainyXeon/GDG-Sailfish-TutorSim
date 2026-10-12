"""
CÁC MODULE NGHIỆP VỤ (modular monolith). Mỗi module là một thư mục:
  __init__.py  -> API CÔNG KHAI: thứ duy nhất module khác được import
  service.py   -> nghiệp vụ + bảng của riêng module
  router.py    -> endpoint HTTP
  models.py    -> định dạng dữ liệu gửi/nhận (Pydantic)
Quy tắc: `from app.modules.exams import top_misconceptions` (ĐÚNG)
         `from app.modules.exams.service import ...` từ module khác (SAI, test_boundaries.py sẽ báo)
"""
