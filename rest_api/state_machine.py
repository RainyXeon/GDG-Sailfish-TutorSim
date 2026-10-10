"""
STATE MACHINE - trang thai hieu cua hoc sinh ao (ported tu prototype/state_machine.py)
CODE THUAN, KHONG dung LLM. LLM chi bao "gia su da thoa dieu kien so may",
con viec hoc sinh hieu hay chua do code o day quyet dinh.

Quy tac v1 (team co the sua):
- Chua thoa dieu kien nao      -> chua_nhan_ra
- Thoa mot phan dieu kien       -> nghi_ngo
- Thoa du tat ca dieu kien      -> da_hieu
- Luot nao gia su noi sai toan  -> khong ghi nhan tien bo o luot do
- Dieu kien da thoa thi giu nguyen (hoc sinh khong "quen" trong 1 phien)
"""

CHUA_NHAN_RA = "chua_nhan_ra"
NGHI_NGO = "nghi_ngo"
DA_HIEU = "da_hieu"


class KnowledgeState:
    def __init__(self, n_conditions):
        self.n = n_conditions
        self.satisfied = set()
        self.log = []  # luu lai tung luot de xem lai khi thu nghiem

    @property
    def state(self):
        if len(self.satisfied) == 0:
            return CHUA_NHAN_RA
        if len(self.satisfied) < self.n:
            return NGHI_NGO
        return DA_HIEU

    def update(self, newly_satisfied, tutor_math_ok=True):
        before = self.state
        if tutor_math_ok:
            for i in newly_satisfied:
                if 0 <= i < self.n:
                    self.satisfied.add(i)
        self.log.append({"before": before, "after": self.state,
                         "satisfied": sorted(self.satisfied), "math_ok": tutor_math_ok})
        return self.state
