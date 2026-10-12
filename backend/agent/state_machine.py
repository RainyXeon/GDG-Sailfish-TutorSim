"""
STATE MACHINE - trạng thái hiểu của học sinh ảo (CODE THUẦN, không dùng LLM).
LLM chỉ báo "gia sư đã thỏa điều kiện số mấy"; học sinh hiểu hay chưa do code ở đây quyết định.

Quy tắc v2:
- Chưa thỏa điều kiện nào                    -> chua_nhan_ra
- Thỏa một phần điều kiện                     -> nghi_ngo
- Thỏa đủ điều kiện VÀ đủ số lượt thuyết phục -> da_hieu
- Mỗi lượt chỉ lên tối đa 1 nấc; chỉ lên ở lượt gia sư thỏa ít nhất 1 điều kiện
- Lượt gia sư nói sai toán -> không ghi nhận tiến bộ
- Lượt gia sư giải hộ toàn bộ -> chỉ ghi nhận tối đa 1 điều kiện
- Tính cách khó cần thêm lượt (extra_turns); trạng thái không đi lùi
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

    @property
    def state(self):
        return self._state

    @property
    def turns_needed(self):
        return 2 + self.extra_turns

    def _target(self):
        if not self.satisfied:
            return CHUA_NHAN_RA
        if len(self.satisfied) < self.n or self.convincing_turns < self.turns_needed:
            return NGHI_NGO
        return DA_HIEU

    def update(self, satisfied_this_turn, tutor_math_ok=True, gives_away=False):
        before = self._state
        valid = [i for i in satisfied_this_turn if isinstance(i, int) and 0 <= i < self.n]
        if gives_away:
            ordered = [i for i in valid if i not in self.satisfied] + [i for i in valid if i in self.satisfied]
            valid = ordered[: self.max_gain_if_gives_away]
        if tutor_math_ok and valid:
            self.satisfied.update(valid)
            self.convincing_turns += 1
            now, target = ORDER.index(before), ORDER.index(self._target())
            self._state = ORDER[max(now, min(target, now + 1))]
        return self._state

    # ---- lưu / đọc lại từ database ----
    def to_dict(self):
        return {"n": self.n, "extra_turns": self.extra_turns, "max_gain_if_gives_away": self.max_gain_if_gives_away,
                "satisfied": sorted(self.satisfied), "convincing_turns": self.convincing_turns, "state": self._state}

    @classmethod
    def from_dict(cls, d):
        s = cls(d["n"], d.get("extra_turns", 0), d.get("max_gain_if_gives_away", 1))
        s.satisfied = set(d.get("satisfied", []))
        s.convincing_turns = d.get("convincing_turns", 0)
        s._state = d.get("state", CHUA_NHAN_RA)
        return s
