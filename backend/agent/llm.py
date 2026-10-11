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
    pass


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
                               http_options=types.HttpOptions(timeout=settings.llm_timeout_sec * 1000))
    return _client


def _call(model, contents, config, retries=None):
    retries = retries or settings.llm_retries
    last = None
    for attempt in range(retries):
        try:
            t0 = time.time()
            resp = _client_().models.generate_content(model=model, contents=contents, config=config)
            resp._latency_ms = int((time.time() - t0) * 1000)
            return resp
        except LLMError:
            raise
        except Exception as e:  # quá tải (429/503), mạng chập chờn... thử lại
            last = e
            msg = str(e)
            if "404" in msg or "API key not valid" in msg or "PERMISSION_DENIED" in msg:
                break  # sai tên model / sai key: thử lại cũng vô ích
            if attempt < retries - 1:
                time.sleep(2 * (attempt + 1))
    raise LLMError(f"Gemini lỗi sau {retries} lần thử: {last}")


def _no_afc(types):
    return types.AutomaticFunctionCallingConfig(disable=True)


def ask_text(prompt, temperature=0.8, fake="[GIẢ] Dạ... em chưa hiểu lắm ạ.", model=None):
    if settings.fake_llm:
        return fake
    from google.genai import types
    resp = _call(model or settings.model, prompt,
                 types.GenerateContentConfig(temperature=temperature, automatic_function_calling=_no_afc(types)))
    return (resp.text or "").strip()


def ask_json(prompt, schema, temperature=0.2, fake=None, model=None):
    if settings.fake_llm:
        return schema.model_validate(fake)
    from google.genai import types
    config = types.GenerateContentConfig(
        temperature=temperature, response_mime_type="application/json", response_schema=schema,
        automatic_function_calling=_no_afc(types))
    resp = _call(model or settings.model, prompt, config)
    if getattr(resp, "parsed", None) is not None:
        return resp.parsed
    return schema.model_validate_json(resp.text)


def ask_with_tools(prompt, tools, temperature=0.3, model=None, retries=1):
    """Gemini tự quyết định gọi hàm nào (automatic function calling).
    Trả về (văn bản cuối, danh sách lời gọi tool để ghi nhật ký)."""
    from google.genai import types
    config = types.GenerateContentConfig(
        temperature=temperature, tools=tools,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(maximum_remote_calls=4))
    resp = _call(model or settings.model_strong, prompt, config, retries=retries)
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
