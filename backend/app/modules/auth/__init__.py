"""MODULE AUTH: tài khoản, mật khẩu, JWT, phân quyền theo vai (tutor, student, manager)."""
from .deps import current_user, require_role, require_self_or_manager
from .service import get_user, list_users, login, register, user_code

__all__ = ["current_user", "require_role", "require_self_or_manager", "get_user", "list_users", "login", "register",
           "user_code"]
