from app.modules.auth import list_users
from app.modules.exams import top_misconceptions_for_center
from app.modules.tutoring import tutor_stats


def tutors_overview():
    return [{"tutor_id": t["id"], "name": t["name"], **tutor_stats(t["id"])} for t in list_users("tutor")]


def center_misconceptions(limit=10):
    return top_misconceptions_for_center(limit)
