from agent.state_machine import KnowledgeState, CHUA_NHAN_RA, NGHI_NGO, DA_HIEU


def test_bat_dau_chua_nhan_ra():
    assert KnowledgeState(2).state == CHUA_NHAN_RA


def test_khong_nhay_thang_len_da_hieu_trong_1_luot():
    assert KnowledgeState(2).update([0, 1]) == NGHI_NGO


def test_luot_thu_hai_thuyet_phuc_thi_hieu():
    s = KnowledgeState(2)
    s.update([0, 1])
    assert s.update([1]) == DA_HIEU


def test_noi_dung_roi_em_khong_lam_nam_tu_hieu():
    s = KnowledgeState(2)
    s.update([0, 1])
    assert s.update([]) == NGHI_NGO


def test_hay_cai_can_them_mot_luot():
    s = KnowledgeState(2, extra_turns=1)
    s.update([0, 1]); s.update([0, 1])
    assert s.state == NGHI_NGO
    assert s.update([1]) == DA_HIEU


def test_giai_ho_chi_ghi_nhan_1_dieu_kien():
    s = KnowledgeState(2)
    s.update([0, 1], gives_away=True)
    assert s.satisfied == {0}


def test_noi_sai_toan_thi_khong_tien_bo():
    assert KnowledgeState(2).update([0, 1], tutor_math_ok=False) == CHUA_NHAN_RA


def test_khong_di_lui():
    s = KnowledgeState(2)
    s.update([0])
    assert s.update([], tutor_math_ok=False) == NGHI_NGO


def test_luu_va_doc_lai():
    s = KnowledgeState(3, extra_turns=1)
    s.update([0, 2])
    t = KnowledgeState.from_dict(s.to_dict())
    assert (t.state, t.satisfied, t.convincing_turns, t.turns_needed) == (NGHI_NGO, {0, 2}, 1, 3)
