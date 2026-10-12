import { useEffect, useRef, useState } from "react";

// Nhúng GeoGebra Apps API. Lệnh vẽ lấy từ cột "geogebra" trong data/misconceptions/*.csv
// (backend trả về trong geogebra_commands). Bài Oxyz dùng bản 3D, bài hàm số dùng bản đồ thị.
const SCRIPT = "https://www.geogebra.org/apps/deployggb.js";
let loading = null;
function loadScript() {
  if (window.GGBApplet) return Promise.resolve();
  if (!loading) {
    loading = new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = SCRIPT;
      s.onload = resolve;
      s.onerror = () => { loading = null; reject(new Error("Không tải được GeoGebra")); };
      document.head.appendChild(s);
    });
  }
  return loading;
}

let counter = 0;
export default function GeoGebra({ commands }) {
  const id = useRef(`ggb-${++counter}`);
  const box = useRef(null);
  const [error, setError] = useState("");
  const is3d = commands.some((c) => /z|\(\s*-?[\d/]+\s*,\s*-?[\d/]+\s*,\s*-?[\d/]+\s*\)/.test(c));

  useEffect(() => {
    let alive = true;
    loadScript()
      .then(() => {
        if (!alive || !box.current) return;
        const width = Math.max(260, box.current.clientWidth);
        const applet = new window.GGBApplet({
          appName: is3d ? "3d" : "graphing", width, height: 320,
          showToolBar: false, showAlgebraInput: false, showMenuBar: false, showResetIcon: true,
          enableShiftDragZoom: true, language: "vi",
          appletOnLoad: (api) => commands.forEach((c) => { try { api.evalCommand(c); } catch { /* bỏ qua lệnh lỗi */ } }),
        }, true);
        applet.inject(id.current);
      })
      .catch((e) => setError(e.message));
    return () => { alive = false; };
  }, [commands.join("|")]);

  if (!commands.length) return <p className="muted">Bài này chưa có hình minh họa.</p>;
  return (
    <div ref={box}>
      {error ? <p className="muted">{error}. Lệnh vẽ: <code>{commands.join("; ")}</code></p> : <div id={id.current} />}
    </div>
  );
}
