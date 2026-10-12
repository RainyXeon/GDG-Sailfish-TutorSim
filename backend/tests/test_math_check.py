import sympy as sp
from agent.classifier import MathClaim
from agent.math_check import check_derivative, extremum_points, distance_point_plane, verify


def test_dao_ham():
    assert check_derivative("x**3 - 3", "3*x**2")
    assert check_derivative("x^3 - 3", "3x^2")          # viết kiểu học sinh vẫn đọc được
    assert not check_derivative("x**3 - 3", "3*x")


def test_cuc_tri():
    assert extremum_points("x**3 - 3") == []
    assert extremum_points("x**3 - 3*x") == [-1, 1]


def test_khoang_cach():
    assert distance_point_plane((1, 2, 3), (2, -1, 2, 1)) == sp.Rational(7, 3)


def test_verify_bat_loi_va_bo_qua_bieu_thuc_la():
    ok, w = verify([MathClaim(kind="cuc_tri", ham_so="x**3 - 3", gia_tri_khang_dinh="0")])
    assert not ok and "không có cực trị" in w[0]
    ok, w = verify([MathClaim(kind="cuc_tri", ham_so="x**3 - 3", gia_tri_khang_dinh="none")])
    assert ok
    ok, w = verify([MathClaim(kind="dao_ham", ham_so="@@@", gia_tri_khang_dinh="3x")])
    assert ok and w == []                                # không đọc được -> không phạt oan
    ok, w = verify([MathClaim(kind="khoang_cach_diem_mat_phang", diem=[1, 2, 3], mat_phang=[2, -1, 2, 1], gia_tri_khang_dinh="7")])
    assert not ok
