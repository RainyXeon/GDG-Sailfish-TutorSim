"""
COACH AGENT - phần "agentic": Gemini TỰ gọi công cụ (xem hồ sơ gia sư, lỗi học sinh thật hay mắc,
danh sách lựa chọn) rồi quyết định bài luyện tiếp theo, kèm lý do.
Nếu Gemini lỗi / chọn bậy / đang FAKE_LLM -> dùng luật dự phòng (cùng nguyên tắc), ghi rõ nguồn.
"""
from .library import MISCONCEPTIONS, PERSONAS, RUBRIC
from .llm import ask_with_tools, extract_json, load_prompt
from settings import settings

WEAK_TO_PERSONA = {"goi_mo": "thu_dong", "thai_do": "hay_cai", "ro_rang": "mat_goc",
                   "chan_doan": "nhanh_nhung_au", "chinh_xac": "mat_goc"}
CRIT_NAME = {r["key"]: r["ten"] for r in RUBRIC}


def _options(chuyen_de):
    mis = [{"id": m["id"], "ten_loi": m["ten_loi"], "dang_bai": m["dang_bai"]}
           for m in MISCONCEPTIONS.values() if m["chuyen_de"] == chuyen_de]
    return {"misconceptions": mis, "personas": {k: v["ten"] for k, v in PERSONAS.items()}}


def rule_based(chuyen_de, profile, center_top):
    """Luật dự phòng, minh bạch, không dùng LLM."""
    avg = profile.get("avg_scores") or {}
    practiced = set(profile.get("practiced_misconceptions") or [])
    if avg:
        weak = min(avg, key=lambda k: avg[k])
        persona = WEAK_TO_PERSONA.get(weak, "thu_dong")
        why_p = f"tiêu chí yếu nhất là '{CRIT_NAME.get(weak, weak)}' ({avg[weak]:.1f}/4)"
    else:
        persona, why_p = "thu_dong", "gia sư mới, bắt đầu với học sinh thụ động"
    pool = [m for m in MISCONCEPTIONS.values() if m["chuyen_de"] == chuyen_de]
    ids = {m["id"] for m in pool}
    center = [c["id"] for c in center_top if c["id"] in ids and c["id"] not in practiced]
    if center:
        mid, why_m = center[0], "là lỗi học sinh của trung tâm hay mắc nhất mà bạn chưa luyện"
    else:
        fresh = [m["id"] for m in pool if m["id"] not in practiced] or [m["id"] for m in pool]
        mid, why_m = fresh[0], "bạn chưa luyện lỗi này"
    return {"misconception_id": mid, "persona": persona,
            "reason": f"Giao học sinh {PERSONAS[persona]['ten'].lower()} vì {why_p}; lỗi {mid} {why_m}.",
            "source": "rule", "tool_calls": []}


def plan_next(tutor_id, chuyen_de, profile, center_top):
    """profile: {avg_scores, practiced_misconceptions, sessions}; center_top: [{id, name, count}]"""
    if settings.fake_llm:
        return rule_based(chuyen_de, profile, center_top)

    def get_tutor_profile() -> dict:
        """Điểm trung bình từng tiêu chí (thang 1-4) của gia sư qua 3 buổi gần nhất và các mã lỗi đã luyện."""
        return profile

    def get_center_top_misconceptions() -> list:
        """Các lỗi sai học sinh thật của trung tâm hay mắc nhất (từ bài luyện đề), kèm số lần."""
        return center_top

    def list_options() -> dict:
        """Danh sách mã lỗi sai trong chuyên đề hiện tại và các tính cách học sinh có thể giao."""
        return _options(chuyen_de)

    try:
        prompt = load_prompt("coach", tutor_id=tutor_id, chuyen_de=chuyen_de)
        text, calls = ask_with_tools(prompt, [get_tutor_profile, get_center_top_misconceptions, list_options])
        d = extract_json(text)
        m, p = d.get("misconception_id"), d.get("persona")
        if m in MISCONCEPTIONS and MISCONCEPTIONS[m]["chuyen_de"] == chuyen_de and p in PERSONAS:
            return {"misconception_id": m, "persona": p, "reason": str(d.get("reason", "")),
                    "source": "agent", "tool_calls": calls}
    except Exception as e:  # Gemini lỗi -> dùng luật, không làm hỏng buổi luyện
        fb = rule_based(chuyen_de, profile, center_top)
        fb["error"] = str(e)[:300]
        return fb
    fb = rule_based(chuyen_de, profile, center_top)
    fb["error"] = "Coach Agent chọn mã không hợp lệ"
    return fb
