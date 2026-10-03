# Chạy: pytest tests
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
import sympy as sp
from math_verifier import check_derivative, extremum_points, distance_point_plane


def test_dao_ham_dung():
    assert check_derivative("x**3 - 3", "3*x**2")


def test_dao_ham_sai():
    assert not check_derivative("x**3 - 3", "3*x")


def test_x_mu_3_khong_co_cuc_tri():
    assert extremum_points("x**3 - 3") == []


def test_x_mu_3_tru_3x_co_hai_cuc_tri():
    assert sorted(extremum_points("x**3 - 3*x")) == [-1, 1]


def test_khoang_cach_diem_mat_phang():
    assert distance_point_plane((1, 2, 3), (2, -1, 2, 1)) == sp.Rational(7, 3)
