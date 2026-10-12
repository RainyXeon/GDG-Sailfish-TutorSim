"""Ghép dữ liệu cho Coach Agent: hồ sơ gia sư (module tutoring truyền vào) + lỗi học sinh hay mắc (module exams)."""
from agent import coach as coach_agent
from app.modules.exams import top_misconceptions_for_center


def plan_next_for(tutor_id, chuyen_de, tutor_profile):
    """Trả về {misconception_id, persona, reason, source: agent|rule, ...}.
    Nhận tutor_profile làm tham số (thay vì tự gọi tutoring) để hai module không gọi vòng qua nhau."""
    return coach_agent.plan_next(tutor_id, chuyen_de, tutor_profile, top_misconceptions_for_center())
