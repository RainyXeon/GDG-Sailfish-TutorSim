# Chạy: pytest tests  (không cần API key)
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from state_machine import KnowledgeState, CHUA_NHAN_RA, NGHI_NGO, DA_HIEU


def test_bat_dau_chua_nhan_ra():
    assert KnowledgeState(2).state == CHUA_NHAN_RA


def test_thoa_mot_phan_la_nghi_ngo():
    s = KnowledgeState(2)
    assert s.update([0]) == NGHI_NGO


def test_thoa_du_la_da_hieu():
    s = KnowledgeState(2)
    s.update([0])
    assert s.update([1]) == DA_HIEU


def test_gia_su_noi_sai_toan_thi_khong_tien_bo():
    s = KnowledgeState(2)
    assert s.update([0, 1], tutor_math_ok=False) == CHUA_NHAN_RA


def test_bo_qua_so_thu_tu_khong_hop_le():
    s = KnowledgeState(2)
    assert s.update([5, -1]) == CHUA_NHAN_RA
