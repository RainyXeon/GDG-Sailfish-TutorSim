"""
KIỂM TRA TOÁN BẰNG SYMPY  (người phụ trách: Tech 7)
Không để LLM tự phán đúng/sai toán. Các hàm ở đây cho đáp án chắc chắn.
Bước tiếp theo (tuần 2): cho LLM trích "phát biểu toán" trong lời gia sư
thành dạng có cấu trúc, rồi gọi các hàm này để kiểm tra.
"""
import sympy as sp

x = sp.symbols("x")


def check_derivative(f_str, claimed_str):
    """Gia sư nói đạo hàm của f là claimed -> đúng hay sai?"""
    f, claimed = sp.sympify(f_str), sp.sympify(claimed_str)
    return sp.simplify(sp.diff(f, x) - claimed) == 0


def extremum_points(f_str, eps=sp.Rational(1, 1000)):
    """Trả về danh sách điểm cực trị thật sự (y' = 0 VÀ y' đổi dấu)."""
    f = sp.sympify(f_str)
    fp = sp.diff(f, x)
    result = []
    for c in sp.solve(sp.Eq(fp, 0), x):
        if not c.is_real:
            continue
        left, right = fp.subs(x, c - eps), fp.subs(x, c + eps)
        if left * right < 0:
            result.append(c)
    return result


def distance_point_plane(point, plane):
    """point = (x0, y0, z0); plane = (a, b, c, d) cho ax + by + cz + d = 0"""
    x0, y0, z0 = point
    a, b, c, d = plane
    return sp.Abs(a * x0 + b * y0 + c * z0 + d) / sp.sqrt(a**2 + b**2 + c**2)


if __name__ == "__main__":
    print("Đạo hàm x^3 - 3 là 3x^2?", check_derivative("x**3 - 3", "3*x**2"))
    print("Cực trị của x^3 - 3:", extremum_points("x**3 - 3"))
    print("Cực trị của x^3 - 3x:", extremum_points("x**3 - 3*x"))
    print("Khoảng cách A(1;2;3) đến 2x - y + 2z + 1 = 0:", distance_point_plane((1, 2, 3), (2, -1, 2, 1)))
