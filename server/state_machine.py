"""
STATE MACHINE - trang thai hieu cua hoc sinh ao (ported tu prototype/state_machine.py)
CODE THUAN, KHONG dung LLM. LLM chi bao "gia su da thoa dieu kien so may",
con viec hoc sinh hieu hay chua do code o day quyet dinh.

Quy tắc v2 (sửa sau khi thử 'hay_cai' thấy Nam hiểu ngay sau 1 tin nhắn):
- Chưa thỏa điều kiện nào                       -> chua_nhan_ra
- Thỏa một phần điều kiện                        -> nghi_ngo
- Thỏa đủ điều kiện VÀ đủ số lượt thuyết phục    -> da_hieu
- MỖI LƯỢT CHỈ LÊN TỐI ĐA 1 NẤC (không nhảy thẳng từ chua_nhan_ra lên da_hieu)
- Chỉ lên nấc ở lượt "thuyết phục" (lượt gia sư thỏa ít nhất 1 điều kiện).
  Gia sư chỉ nói "đúng rồi em" thì Nam không tự hiểu thêm.
- Lượt gia sư nói sai toán -> không ghi nhận tiến bộ
- Lượt gia sư nói luôn toàn bộ đáp án (giải hộ) -> chỉ ghi nhận tối đa 1 điều kiện
- Tính cách khó (hay_cai, mat_goc) cần thêm lượt thuyết phục (extra_turns)
- Trạng thái không bao giờ đi lùi trong 1 phiên
"""

CHUA_NHAN_RA = "chua_nhan_ra"
NGHI_NGO = "nghi_ngo"
DA_HIEU = "da_hieu"
ORDER = [CHUA_NHAN_RA, NGHI_NGO, DA_HIEU]


class KnowledgeState:
    def __init__(self, n_conditions, extra_turns=0, max_gain_if_gives_away=1):
        self.n = n_conditions
        self.extra_turns = extra_turns
        self.max_gain_if_gives_away = max_gain_if_gives_away
        self.satisfied = set()
        self.convincing_turns = 0
        self._state = CHUA_NHAN_RA
        self.log = []

    @property
    def state(self):
        return self._state

    @property
    def turns_needed(self):
        """Số lượt thuyết phục tối thiểu để hiểu: 2 (vì mỗi lượt lên 1 nấc) + thêm theo tính cách."""
        return 2 + self.extra_turns

    def _target(self):
        if not self.satisfied:
            return CHUA_NHAN_RA
        if len(self.satisfied) < self.n or self.convincing_turns < self.turns_needed:
            return NGHI_NGO
        return DA_HIEU

    def update(self, satisfied_this_turn, tutor_math_ok=True, gives_away=False):
        before = self._state
        valid = [i for i in satisfied_this_turn if 0 <= i < self.n]
        if gives_away:
            # ưu tiên ghi nhận điều kiện mới, nhưng chỉ tối đa max_gain_if_gives_away
            ordered = [i for i in valid if i not in self.satisfied] + [i for i in valid if i in self.satisfied]
            valid = ordered[: self.max_gain_if_gives_away]
        convincing = tutor_math_ok and len(valid) > 0
        if convincing:
            self.satisfied.update(valid)
            self.convincing_turns += 1
            target = ORDER.index(self._target())
            now = ORDER.index(before)
            self._state = ORDER[max(now, min(target, now + 1))]  # tối đa lên 1 nấc, không đi lùi
        self.log.append({"before": before, "after": self._state, "satisfied": sorted(self.satisfied),
                         "convincing_turns": self.convincing_turns, "math_ok": tutor_math_ok, "gives_away": gives_away})
        return self._state
