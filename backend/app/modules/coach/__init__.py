"""MODULE COACH: chọn bài luyện tiếp theo cho gia sư (Coach Agent + luật dự phòng). Không có bảng, không có endpoint riêng."""
from .service import plan_next_for, plan_next_rule_for

__all__ = ["plan_next_for", "plan_next_rule_for"]
