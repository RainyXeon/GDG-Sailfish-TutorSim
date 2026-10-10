"""
DU LIEU CHO API (ported tu prototype/data.py, nguoi phu trach goc: Tech 5)
- MISCONCEPTIONS: thu vien loi sai (tam viet tay, sau nay doc tu CSV)
- PERSONAS: tinh cach hoc sinh ao
- RUBRIC: 5 tieu chi cham gia su
"""
import csv

MISCONCEPTIONS = [
    {
        "id": "HS-01",
        "chuyen_de": "ham_so",
        "ten_loi": "Cho rằng f'(x0) = 0 thì x0 chắc chắn là điểm cực trị",
        "bai_toan": "Tìm các điểm cực trị của hàm số y = x^3 - 3",
        "loi_giai_sai": "y' = 3x^2. Cho y' = 0 <=> x = 0. Vậy hàm số đạt cực trị tại x = 0.",
        "nguyen_nhan_goc": "Nhầm điều kiện cần thành điều kiện đủ, không xét dấu y'",
        "dieu_kien_hieu_ra": [
            "Gia sư chỉ ra (hoặc dẫn dắt để học sinh nhận ra) y' = 0 chỉ là điều kiện cần, chưa đủ để kết luận cực trị",
            "Gia sư hướng dẫn xét dấu y' ở hai bên x = 0 (lập bảng biến thiên) hoặc đưa ra phản ví dụ, để thấy y' không đổi dấu",
        ],
    },
    {
        "id": "OX-01",
        "chuyen_de": "oxyz",
        "ten_loi": "Tính khoảng cách từ điểm đến mặt phẳng nhưng quên chia cho độ dài vectơ pháp tuyến",
        "bai_toan": "Tính khoảng cách từ điểm A(1; 2; 3) đến mặt phẳng (P): 2x - y + 2z + 1 = 0",
        "loi_giai_sai": "d = |2.1 - 2 + 2.3 + 1| = |7| = 7.",
        "nguyen_nhan_goc": "Nhớ thiếu công thức, không hiểu ý nghĩa của mẫu số căn(a^2 + b^2 + c^2)",
        "dieu_kien_hieu_ra": [
            "Gia sư chỉ ra lời giải thiếu mẫu số căn(a^2 + b^2 + c^2) trong công thức khoảng cách",
            "Gia sư giải thích vì sao cần chia (chuẩn hóa vectơ pháp tuyến) hoặc dẫn dắt học sinh tự viết lại công thức đầy đủ",
        ],
    },
]

PERSONAS = {
    "thu_dong": "Thụ động, ít nói, trả lời ngắn kiểu 'dạ', 'vâng ạ', ít khi tự hỏi. Nếu gia sư chỉ giảng mà không hỏi thì em cứ 'dạ' cho qua dù chưa hiểu.",
    "hay_cai": "Hay cãi, tự tin vào lời giải của mình, hay nói 'nhưng thầy cô trên lớp dạy thế mà', đòi gia sư chứng minh.",
    "mat_goc": "Mất gốc, hay lẫn khái niệm cơ bản, dễ bối rối khi gia sư dùng thuật ngữ khó, hay hỏi 'cái đó là gì ạ'.",
    "nhanh_nhung_au": "Hiểu nhanh nhưng ẩu, hay gật đầu vội 'em hiểu rồi' rồi lại nói sai ở chi tiết.",
}

RUBRIC = [
    {"key": "chinh_xac", "ten": "Chính xác chuyên môn", "trong_so": 0.20,
     "muc": {1: "Nói sai kiến thức", 2: "Có chỗ không chính xác", 3: "Đúng nhưng thiếu chặt chẽ", 4: "Hoàn toàn chính xác, chặt chẽ"}},
    {"key": "chan_doan", "ten": "Chẩn đoán lỗi sai", "trong_so": 0.25,
     "muc": {1: "Không tìm ra lỗi", 2: "Chỉ nói 'sai rồi'", 3: "Chỉ đúng chỗ sai", 4: "Chỉ đúng chỗ sai và nguyên nhân gốc"}},
    {"key": "ro_rang", "ten": "Rõ ràng trong giải thích", "trong_so": 0.20,
     "muc": {1: "Khó hiểu, lộn xộn", 2: "Hiểu được nhưng dài dòng", 3: "Mạch lạc", 4: "Mạch lạc, hợp trình độ, có ví dụ"}},
    {"key": "goi_mo", "ten": "Kỹ năng gợi mở", "trong_so": 0.20,
     "muc": {1: "Giải hộ toàn bộ", 2: "Chủ yếu giảng một chiều", 3: "Có câu hỏi dẫn dắt", 4: "Học sinh tự nhận ra lỗi nhờ câu hỏi dẫn dắt"}},
    {"key": "thai_do", "ten": "Thái độ & xử lý tình huống", "trong_so": 0.15,
     "muc": {1: "Thiếu kiên nhẫn, chê bai", 2: "Trung tính", 3: "Kiên nhẫn, khích lệ", 4: "Kiên nhẫn, xử lý khéo khi học sinh cãi hoặc bối rối"}},
]


def find_misconception(misconception_id):
    return next((m for m in MISCONCEPTIONS if m["id"] == misconception_id), None)


def load_misconceptions_csv(path):
    """Dùng sau khi có file CSV xuất từ Google Sheets.
    Cột dieu_kien_hieu_ra: các điều kiện cách nhau bằng dấu ';'"""
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["dieu_kien_hieu_ra"] = [s.strip() for s in r["dieu_kien_hieu_ra"].split(";") if s.strip()]
    return rows
