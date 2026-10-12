"""Giữ ranh giới modular monolith: module chỉ được import API CÔNG KHAI (__init__.py) của module khác."""
import re
from pathlib import Path

MODULES = Path(__file__).resolve().parents[1] / "app" / "modules"
IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+app\.modules\.(\w+)(\.\w+)?", re.M)


def test_khong_import_ruot_module_khac():
    bad = []
    for f in MODULES.rglob("*.py"):
        own = f.relative_to(MODULES).parts[0]
        for other, sub in IMPORT_RE.findall(f.read_text(encoding="utf-8")):
            if other != own and sub:
                bad.append(f"{f.relative_to(MODULES)} -> app.modules.{other}{sub}")
    assert not bad, "Chỉ import từ app.modules.<tên> (API công khai), không import file bên trong:\n" + "\n".join(bad)


def test_module_khong_dung_bang_cua_module_khac():
    owners = {"auth": {"users"}, "tutoring": {"sessions", "messages", "reports"}, "exams": {"attempts"}}
    bad = []
    for f in MODULES.rglob("*.py"):
        own = f.relative_to(MODULES).parts[0]
        sql = f.read_text(encoding="utf-8")
        for mod, tables in owners.items():
            if mod == own:
                continue
            for t in tables:
                if re.search(rf"\b(FROM|JOIN|INTO|UPDATE)\s+{t}\b", sql):
                    bad.append(f"{f.relative_to(MODULES)} dùng bảng '{t}' của module {mod}")
    assert not bad, "\n".join(bad)


def test_main_chi_ghep_router():
    main = (MODULES.parent / "main.py").read_text(encoding="utf-8")
    assert "db." not in main and "agent" not in main.split('"""', 2)[2]
