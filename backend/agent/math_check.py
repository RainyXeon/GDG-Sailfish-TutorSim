"""
KIỂM TRA TOÁN BẰNG SYMPY - không để LLM tự phán đúng/sai.
Chỉ cảnh báo khi CHẮC CHẮN sai; biểu thức không đọc được thì bỏ qua (không phạt oan gia sư).
"""
import sympy as sp
from sympy.parsing.sympy_parser import (parse_expr, standard_transformations,
                                        implicit_multiplication_application, convert_xor)

x = sp.symbols("x", real=True)
_T = standard_transformations + (implicit_multiplication_application, convert_xor)


def _p(s):
    return parse_expr(str(s).replace("√", "sqrt").replace("−", "-"), transformations=_T, local_dict={"x": x})


def check_derivative(f_str, claimed_str):
    return sp.simplify(sp.diff(_p(f_str), x) - _p(claimed_str)) == 0


def extremum_points(f_str, eps=sp.Rational(1, 1000)):
    f = _p(f_str)
    fp = sp.diff(f, x)
    pts = []
    for c in sp.solve(sp.Eq(fp, 0), x):
        if c.is_real and (fp.subs(x, c - eps) * fp.subs(x, c + eps)) < 0:
            pts.append(sp.nsimplify(c))
    return sorted(pts)


def distance_point_plane(point, plane):
    x0, y0, z0 = [sp.nsimplify(v) for v in point]
    a, b, c, d = [sp.nsimplify(v) for v in plane]
    return sp.Abs(a * x0 + b * y0 + c * z0 + d) / sp.sqrt(a**2 + b**2 + c**2)


def verify(claims):
    """claims: list[MathClaim]. Trả về (math_ok, warnings)."""
    warnings = []
    for c in claims or []:
        try:
            if c.kind == "dao_ham" and c.ham_so and c.gia_tri_khang_dinh:
                if not check_derivative(c.ham_so, c.gia_tri_khang_dinh):
                    real = sp.diff(_p(c.ham_so), x)
                    warnings.append(f"Đạo hàm của {c.ham_so} là {sp.sstr(real)}, không phải {c.gia_tri_khang_dinh}.")
            elif c.kind == "cuc_tri" and c.ham_so and c.gia_tri_khang_dinh is not None:
                real = extremum_points(c.ham_so)
                txt = c.gia_tri_khang_dinh.strip().lower()
                said = [] if txt in ("none", "không", "không có", "") else sorted(sp.nsimplify(_p(v)) for v in txt.split(","))
                same = len(said) == len(real) and all(sp.simplify(a - b) == 0 for a, b in zip(said, real))
                if not same:
                    real_txt = ", ".join(sp.sstr(v) for v in real) or "không có cực trị"
                    warnings.append(f"Hàm {c.ham_so}: điểm cực trị đúng là {real_txt}.")
            elif c.kind == "khoang_cach_diem_mat_phang" and c.diem and c.mat_phang and c.gia_tri_khang_dinh:
                real = distance_point_plane(c.diem, c.mat_phang)
                if abs(float(real) - float(_p(c.gia_tri_khang_dinh))) > 1e-6:
                    warnings.append(f"Khoảng cách đúng là {sp.sstr(sp.nsimplify(real))}, không phải {c.gia_tri_khang_dinh}.")
        except Exception:
            continue  # không đọc được biểu thức -> bỏ qua
    return len(warnings) == 0, warnings
