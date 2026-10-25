"""
Gọi Gemini - gom vào 1 chỗ.
- ask_text: văn bản (học sinh ảo)
- ask_json: JSON theo schema Pydantic (phân loại, chấm điểm)
- ask_with_tools: cho Gemini tự gọi các hàm Python (Coach Agent)
FAKE_LLM=1: không gọi mạng, trả về giá trị giả để test luồng.
"""
import json
import logging
import re
import time
from pathlib import Path
from string import Template

from settings import settings

PROMPT_DIR = Path(__file__).parent / "prompts"
# SDK in cảnh báo vô hại mỗi lần dùng function calling tự động; tắt cho log gọn
logging.getLogger("google_genai.models").setLevel(logging.ERROR)
_client = None


class LLMError(RuntimeError):
    """Lỗi khi gọi Gemini. kind: quota | overloaded | timeout | auth | bad_output | other.
    retry_after: số giây nên chờ trước khi thử lại (nếu biết), để API trả header Retry-After."""

    def __init__(self, message, kind="other", retry_after=None):
        super().__init__(message)
        self.kind, self.retry_after = kind, retry_after


def load_prompt(name, **values):
    """Đọc agent/prompts/<name>.md mỗi lần gọi -> sửa prompt không cần khởi động lại server."""
    text = (PROMPT_DIR / f"{name}.md").read_text(encoding="utf-8")
    return Template(text).safe_substitute(**values)


def _client_():
    global _client
    if _client is None:
        if not settings.gemini_api_key:
            raise LLMError("Thiếu GEMINI_API_KEY trong backend/.env (hoặc đặt FAKE_LLM=1 để chạy thử).")
        from google import genai
        from google.genai import types
        _client = genai.Client(api_key=settings.gemini_api_key,
                               http_options=types.HttpOptions(timeout=settings.llm_timeout_sec * 1000,base_url="https://ckey.vn"))
    return _client


_RETRY_DELAY_RE = re.compile(r"retryDelay['\"]?\s*[:=]\s*['\"]?(\d+(?:\.\d+)?)s")


def _status_of(e):
    """Mã HTTP của lỗi Gemini (429, 503...) hoặc None nếu là lỗi mạng / timeout."""
    code = getattr(e, "code", None)
    if isinstance(code, int):
        return code
    m = re.match(r"\s*(\d{3})\b", str(e))
    return int(m.group(1)) if m else None


def _classify_error(e):
    """-> (kind, nên_thử_lại, số_giây_chờ_gợi_ý)."""
    msg, code = str(e), _status_of(e)
    if code == 429 or "RESOURCE_EXHAUSTED" in msg:
        m = _RETRY_DELAY_RE.search(msg)
        delay = float(m.group(1)) if m else None
        if "PerDay" in msg or "per day" in msg.lower():
            return "quota", False, delay           # hết hạn mức trong NGÀY: thử lại vô ích
        return "quota", True, delay                # hết hạn mức theo PHÚT: chờ rồi thử lại
    if code in (401, 403, 404) or "API key not valid" in msg or "PERMISSION_DENIED" in msg:
        return "auth", False, None                 # sai key / sai tên model
    if code == 400:
        return "other", False, None
    if code in (500, 502, 503, 504) or "UNAVAILABLE" in msg or "overloaded" in msg.lower():
        return "overloaded", True, None
    if "timed out" in msg.lower() or "timeout" in type(e).__name__.lower():
        return "timeout", True, None
    return "other", True, None                     # mạng chập chờn...


_FRIENDLY = {
    "quota": "Gemini đang hết hạn mức gọi (429). Chờ khoảng 1 phút rồi thử lại.",
    "overloaded": "Máy chủ Gemini đang quá tải.",
    "timeout": "Gemini trả lời quá lâu.",
    "auth": "Sai GEMINI_API_KEY hoặc sai tên model.",
}


def _call(model, contents, config, retries=None, budget_sec=None):
    """Gọi Gemini có thử lại. Tổng thời gian (kể cả lúc chờ) không vượt budget_sec,
    để request không kéo dài quá giới hạn của proxy (Render, nginx... cắt ở ~60-100 giây -> 502/504)."""
    retries = retries or settings.llm_retries
    deadline = time.monotonic() + (budget_sec or settings.llm_call_budget_sec)
    last, kind, hint, attempt = None, "other", None, 0
    while attempt < retries:
        remaining = deadline - time.monotonic()
        if remaining < 3:
            kind = "timeout" if last is None else kind
            break
        try:
            from google.genai import types
            # timeout của TỪNG lần gọi không vượt quá thời gian còn lại của cả lượt
            config.http_options = types.HttpOptions(timeout=int(min(settings.llm_timeout_sec, remaining) * 1000))
            t0 = time.time()
            resp = _client_().models.generate_content(model=model, contents=contents, config=config)
            resp._latency_ms = int((time.time() - t0) * 1000)
            return resp
        except LLMError:
            raise
        except Exception as e:
            last = e
            msg = str(e)
            if getattr(config, "thinking_config", None) is not None and "400" in msg and "hink" in msg:
                _thinking_unsupported.add(model)       # model không hỗ trợ mức suy nghĩ -> gửi lại không có nó
                config.thinking_config = None          # (không tính là một lần thử)
                continue
            kind, retryable, hint = _classify_error(e)
            attempt += 1
            if not retryable or attempt >= retries:
                break
            wait = hint if hint is not None else 2 * attempt
            wait = min(wait, settings.llm_max_retry_wait_sec)
            # còn đủ thời gian cho lần chờ + một lần gọi ngắn nữa thì mới thử lại
            if time.monotonic() + wait + 5 > deadline:
                break
            logging.getLogger("tutorsim.llm").warning("Gemini lỗi (%s), thử lại sau %.0fs: %s", kind, wait, msg[:200])
            time.sleep(wait)
    friendly = _FRIENDLY.get(kind, "Gemini lỗi.")
    detail = str(last)[:300] if last else "hết thời gian cho phép"
    raise LLMError(f"{friendly} (chi tiết: {detail})", kind=kind,
                   retry_after=int(hint) + 1 if hint else (60 if kind == "quota" else None))


def _no_afc(types):
    return types.AutomaticFunctionCallingConfig(disable=True)


_thinking_unsupported = set()  # model không nhận tham số suy nghĩ -> lần sau khỏi gửi


def _thinking(types, model, strong=False):
    """Giảm thời gian "suy nghĩ" của model: việc phân loại, đóng vai không cần nghĩ sâu.
    Model nào không hỗ trợ thì bỏ qua (xem _call)."""
    level = settings.thinking_strong if strong else settings.thinking
    if level in ("", "off", "none") or model in _thinking_unsupported:
        return None
    return types.ThinkingConfig(thinking_level=level.upper())


def _config(types, model, strong=False, **kw):
    cfg = types.GenerateContentConfig(**kw)
    t = _thinking(types, model, strong)
    if t is not None:
        cfg.thinking_config = t
    return cfg


def ask_text(prompt, temperature=0.8, fake="[GIẢ] Dạ... em chưa hiểu lắm ạ.", model=None, budget_sec=None):
    if settings.fake_llm:
        return fake
    from google.genai import types
    model = model or settings.model
    resp = _call(model, prompt, _config(types, model, temperature=temperature, automatic_function_calling=_no_afc(types)),
                 budget_sec=budget_sec)
    try:
        return (resp.text or "").strip()
    except Exception:  # bị chặn bởi bộ lọc an toàn -> không có text
        return ""


def ask_json(prompt, schema, temperature=0.2, fake=None, model=None, strong=False, budget_sec=None):
    if settings.fake_llm:
        return schema.model_validate(fake)
    from google.genai import types
    import re

    model = model or settings.model
    
    # 1. Ép thêm system_instruction cứng vào config
    # Đảm bảo Gemini luôn giữ vai trò là một JSON Serializer thuần túy
    json_system_instruction = (
        "You are a precise JSON generator. You MUST respond with ONLY a valid JSON object "
        "matching the requested schema. Strictly NO markdown code block wrappers (do not use ```json), "
        "NO introductory or conversational text, and NO trailing explanation."
    )
    
    # Giả sử hàm _config của bạn cho phép truyền system_instruction 
    # Hoặc bạn inject trực tiếp vào config bên trong hàm này
    config = _config(
        types, 
        model, 
        strong=strong, 
        temperature=temperature, 
        response_mime_type="application/json", 
        response_schema=schema,
        automatic_function_calling=_no_afc(types)
    )
    
    # Đảm bảo system_instruction được gán trong config object của google.genai
    if hasattr(config, "system_instruction") and not config.system_instruction:
        config.system_instruction = json_system_instruction

    last = None
    deadline = time.monotonic() + (budget_sec or settings.llm_call_budget_sec)
    
    for _ in range(2):
        left = deadline - time.monotonic()
        if left < 5:
            break
            
        resp = _call(model, prompt, config, budget_sec=left)
        
        # Đã parse sẵn qua Pydantic nhờ response_schema
        if getattr(resp, "parsed", None) is not None:
            return resp.parsed
            
        raw_text = (resp.text or "").strip()
        
        # 2. Bắt lớp phòng thủ (Sanitization) - Cắt bỏ câu dẫn tiếng Việt hoặc Markdown block nếu Gemini vẫn vi phạm
        try:
            # Lọc trích xuất đúng vùng chứa ngoặc nhọn JSON { ... }
            match = re.search(r"(\{[\s\S]*\})", raw_text)
            clean_json_str = match.group(1) if match else raw_text
            
            return schema.model_validate_json(clean_json_str)
        except Exception as e:
            last = e
            
    raise LLMError(f"Gemini trả về dữ liệu không đúng định dạng: {str(last)[:200]}", kind="bad_output")


def ask_with_tools(prompt, tools, temperature=0.3, model=None, retries=1):
    """Gemini tự quyết định gọi hàm nào (automatic function calling).
    Trả về (văn bản cuối, danh sách lời gọi tool để ghi nhật ký)."""
    from google.genai import types
    model = model or settings.model_strong
    config = _config(types, model, strong=True, temperature=temperature, tools=tools,
                     automatic_function_calling=types.AutomaticFunctionCallingConfig(maximum_remote_calls=4))
    resp = _call(model, prompt, config, retries=retries, budget_sec=settings.coach_budget_sec)
    calls = []
    for c in getattr(resp, "automatic_function_calling_history", None) or []:
        for part in getattr(c, "parts", None) or []:
            fc = getattr(part, "function_call", None)
            if fc is not None:
                calls.append({"tool": fc.name, "args": dict(fc.args or {})})
    return (resp.text or "").strip(), calls


def extract_json(text):
    """Lấy object JSON đầu tiên trong văn bản (Gemini đôi khi bọc trong ```json)."""
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        raise ValueError("Không thấy JSON trong câu trả lời")
    return json.loads(m.group(0))
