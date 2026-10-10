"""
DỮ LIỆU CHO AGENT: thư viện lỗi sai (đọc từ data/misconceptions/*.csv), tính cách, rubric.
Sửa lỗi sai: sửa file CSV (hoặc Excel rồi chạy scripts/xlsx_to_csv.py), khởi động lại server.
"""
import csv
from settings import DATA_DIR, settings

TOPICS = {"ham_so": "Hàm số", "oxyz": "Hình học Oxyz"}


def _split(s):
    return [p.strip() for p in (s or "").split("|") if p.strip()]


def load_misconceptions():
    items = {}
    for path in sorted((DATA_DIR / "misconceptions").glob("*.csv")):
        with open(path, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if not r.get("id"):
                    continue
                if settings.only_approved and r.get("trang_thai", "").strip() != "Đồng ý":
                    continue
                r["dieu_kien_hieu_ra"] = _split(r.get("dieu_kien_hieu_ra"))
                r["phan_ung_goi_y"] = _split(r.get("phan_ung_goi_y"))
                r["geogebra"] = _split(r.get("geogebra"))
                if len(r["dieu_kien_hieu_ra"]) == 0:
                    continue
                items[r["id"]] = r
    return items


MISCONCEPTIONS = load_misconceptions()

PERSONAS = {
    "thu_dong": {
        "ten": "Thụ động",
        "mo_ta": "Thụ động, ít nói, ít khi tự hỏi. Nếu gia sư chỉ giảng mà không hỏi thì em cứ 'dạ' cho qua dù chưa hiểu.",
        "cach_the_hien": "Trả lời rất ngắn ('dạ', 'vâng ạ', 'em không biết ạ'). Không tự hỏi thêm trừ khi gia sư hỏi trực tiếp. Khi gia sư hỏi một câu cụ thể thì trả lời đúng câu đó, ngắn gọn.",
        "extra_turns": 0,
    },
    "hay_cai": {
        "ten": "Hay cãi",
        "mo_ta": "Tự tin vào lời giải của mình, hay nói 'nhưng thầy cô trên lớp dạy thế mà', đòi gia sư chứng minh.",
        "cach_the_hien": "Khi chưa nhận ra: bảo vệ lời giải bằng lý lẽ cụ thể. Khi đang nghi ngờ: vẫn PHẢN BÁC ít nhất một lần ('thầy chứng minh đi', 'sách ghi thế mà') hoặc đòi ví dụ; không nói 'em hiểu rồi'. Chỉ chịu khi đã hiểu thật.",
        "extra_turns": 1,
    },
    "mat_goc": {
        "ten": "Mất gốc",
        "mo_ta": "Hay lẫn khái niệm cơ bản, dễ bối rối khi gia sư dùng thuật ngữ khó.",
        "cach_the_hien": "Hỏi lại thuật ngữ gia sư vừa dùng ('đổi dấu là sao ạ?', 'điều kiện cần là gì ạ?'). Giải thích dài thì em rối, nói 'em chưa hiểu lắm'.",
        "extra_turns": 1,
    },
    "nhanh_nhung_au": {
        "ten": "Nhanh nhưng ẩu",
        "mo_ta": "Hiểu nhanh nhưng ẩu, hay gật đầu vội 'em hiểu rồi' rồi lại nói sai ở chi tiết.",
        "cach_the_hien": "Hay nói 'à em hiểu rồi' nhưng khi đang nghi ngờ thì diễn đạt lại vẫn sai một chi tiết nhỏ (dấu, điều kiện, đầu mút...).",
        "extra_turns": 0,
    },
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
RUBRIC_KEYS = [r["key"] for r in RUBRIC]


def topic_label(m):
    return f"{TOPICS.get(m['chuyen_de'], m['chuyen_de'])} – {m['dang_bai']}"
