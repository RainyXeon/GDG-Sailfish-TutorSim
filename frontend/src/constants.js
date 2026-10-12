export const CRITERIA = {
  chinh_xac: "Chính xác chuyên môn",
  chan_doan: "Chẩn đoán lỗi sai",
  ro_rang: "Rõ ràng khi giải thích",
  goi_mo: "Gợi mở, không giải hộ",
  thai_do: "Thái độ và xử lý tình huống",
};
export const formatDate = (iso) => {
  if (!iso) return "–";
  const d = new Date(iso);
  return d.toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit" }) + " " +
    d.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });
};
