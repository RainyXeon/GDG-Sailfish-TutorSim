"""Tài khoản, mật khẩu, JWT."""
import app.main  # noqa: F401  (nạp đủ các module + bảng)
import pytest
from app.core.errors import ServiceError
from app.modules import auth
from app.core.security import create_token, decode_token, hash_password, verify_password


def test_bam_mat_khau():
    h = hash_password("mat-khau-dai")
    assert h.startswith("pbkdf2_sha256$") and "mat-khau-dai" not in h
    assert verify_password("mat-khau-dai", h)
    assert not verify_password("sai", h)
    assert hash_password("mat-khau-dai") != h          # có muối: băm 2 lần ra 2 kết quả khác
    assert not verify_password("x", "chuoi-hong")


def test_token():
    user = {"id": 1, "role": "tutor"}
    assert decode_token(create_token(user)) == 1
    assert decode_token("abc.def.ghi") is None
    assert decode_token(create_token(user) + "x") is None   # sửa token -> vô hiệu


def test_dang_ky_dang_nhap():
    r = auth.register("Gia_Su.Moi", "12345678", "Gia sư mới", "tutor")
    assert r["user"]["username"] == "gia_su.moi" and r["user"]["role"] == "tutor"
    assert "password_hash" not in r["user"]
    assert auth.login("gia_su.moi", "12345678")["user"]["id"] == r["user"]["id"]
    with pytest.raises(ServiceError) as e:
        auth.login("gia_su.moi", "sai-mat-khau")
    assert e.value.status == 401


@pytest.mark.parametrize("args, status", [
    (("gia_su.moi", "12345678", "Trùng", "tutor"), 409),     # trùng tên
    (("ab", "12345678", "Ngắn", "tutor"), 400),              # tên quá ngắn
    (("co dau", "12345678", "Có dấu cách", "tutor"), 400),
    (("hople1", "1234", "Mật khẩu ngắn", "tutor"), 400),
    (("hople2", "12345678", "Tự phong quản lý", "manager"), 400),
])
def test_dang_ky_sai(args, status):
    with pytest.raises(ServiceError) as e:
        auth.register(*args)
    assert e.value.status == status


def test_tai_khoan_mau_va_quan_ly():
    assert auth.login("minh", "demo1234")["user"]["role"] == "tutor"
    assert auth.login("ha", "demo1234")["user"]["role"] == "student"
    assert auth.login("quanly", "quanly-mat-khau")["user"]["role"] == "manager"
