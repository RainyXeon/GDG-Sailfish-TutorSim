import { useEffect, useState } from "react";
import { getHealth, login, register } from "../api.js";

// Màn đầu tiên: đăng nhập hoặc tự đăng ký (gia sư / học sinh). Tài khoản quản lý do trung tâm cấp.
export default function Login({ onLoggedIn }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ username: "", password: "", name: "", role: "tutor" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [canRegister, setCanRegister] = useState(true);

  useEffect(() => { getHealth().then((h) => setCanRegister(h.allow_register !== false)).catch(() => {}); }, []);
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const r = mode === "login"
        ? await login(form.username, form.password)
        : await register(form.username, form.password, form.name, form.role);
      onLoggedIn(r.user);
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <section className="narrow">
      <h1 className="title">TutorSim</h1>
      <p className="lead">Gia sư luyện chữa bài với học sinh ảo. Học sinh luyện đề và theo dõi điểm dự kiến.</p>

      {canRegister && (
        <div className="seg auth-seg" role="tablist" aria-label="Đăng nhập hoặc đăng ký">
          <button role="tab" aria-selected={mode === "login"} className={mode === "login" ? "seg-item on" : "seg-item"}
            onClick={() => { setMode("login"); setError(""); }}>Đăng nhập</button>
          <button role="tab" aria-selected={mode === "register"} className={mode === "register" ? "seg-item on" : "seg-item"}
            onClick={() => { setMode("register"); setError(""); }}>Tạo tài khoản</button>
        </div>
      )}

      <form className="auth-form" onSubmit={submit}>
        {mode === "register" && (
          <>
            <label className="field">
              <span>Bạn là</span>
              <div className="seg" role="radiogroup" aria-label="Vai trò">
                {[["tutor", "Gia sư"], ["student", "Học sinh"]].map(([v, label]) => (
                  <button type="button" key={v} role="radio" aria-checked={form.role === v}
                    className={form.role === v ? "seg-item on" : "seg-item"}
                    onClick={() => setForm((f) => ({ ...f, role: v }))}>{label}</button>
                ))}
              </div>
            </label>
            <label className="field">
              <span>Tên hiển thị</span>
              <input value={form.name} onChange={set("name")} required maxLength={60} placeholder="Ví dụ: Minh" />
            </label>
          </>
        )}
        <label className="field">
          <span>Tên đăng nhập</span>
          <input value={form.username} onChange={set("username")} required autoComplete="username"
            autoCapitalize="none" placeholder="chữ thường không dấu, số" />
        </label>
        <label className="field">
          <span>Mật khẩu</span>
          <input type="password" value={form.password} onChange={set("password")} required
            minLength={mode === "register" ? 8 : undefined}
            autoComplete={mode === "login" ? "current-password" : "new-password"}
            placeholder={mode === "register" ? "ít nhất 8 ký tự" : ""} />
        </label>
        {error && <p className="error" role="alert">{error}</p>}
        <button className="btn primary" type="submit" disabled={busy}>
          {busy ? "Đang xử lý…" : mode === "login" ? "Đăng nhập" : "Tạo tài khoản"}
        </button>
      </form>
      <p className="muted small hint-login">Tài khoản quản lý trung tâm do người phụ trách cấp, không tự tạo được.</p>
    </section>
  );
}
