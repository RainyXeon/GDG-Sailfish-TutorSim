"""
STATE MACHINE - trạng thái hiểu của học sinh ảo  (người phụ trách: Tech 2)
CODE THUẦN, KHÔNG dùng LLM. LLM chỉ báo "gia sư đã thỏa điều kiện số mấy",
còn việc học sinh hiểu hay chưa do code ở đây quyết định.

Quy tắc v1 (team có thể sửa):
- Chưa thỏa điều kiện nào      -> chua_nhan_ra
- Thỏa một phần điều kiện       -> nghi_ngo
- Thỏa đủ tất cả điều kiện      -> da_hieu
- Lượt nào gia sư nói sai toán  -> không ghi nhận tiến bộ ở lượt đó
- Điều kiện đã thỏa thì giữ nguyên (học sinh không "quên" trong 1 phiên)
"""

CHUA_NHAN_RA = "chua_nhan_ra"
NGHI_NGO = "nghi_ngo"
DA_HIEU = "da_hieu"


class KnowledgeState:
    def __init__(self, n_conditions):
        self.n = n_conditions
        self.satisfied = set()
        self.log = []  # lưu lại từng lượt để xem lại khi thử nghiệm

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
