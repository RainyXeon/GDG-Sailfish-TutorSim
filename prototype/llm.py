"""
Gọi Gemini - gom vào 1 chỗ  (người phụ trách: Tech 2)
- ask_text: trả về văn bản (dùng cho học sinh ảo)
- ask_json: trả về JSON theo schema Pydantic (dùng cho phân loại, chấm điểm)
Chế độ thử không cần API key: đặt biến môi trường FAKE_LLM=1
"""
import os
import time
from pathlib import Path
from string import Template

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Kiểm tra tên model mới nhất trong Google AI Studio rồi điền vào .env (GEMINI_MODEL=...)
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
FAKE = os.getenv("FAKE_LLM") == "1"
PROMPT_DIR = Path(__file__).parent / "prompts"
_client = None


def load_prompt(name, **values):
    """Đọc prompts/<name>.md và thay các biến $ten_bien bằng giá trị."""
    text = (PROMPT_DIR / f"{name}.md").read_text(encoding="utf-8")
    return Template(text).substitute(**values)


def _get_client():
    global _client
    if _client is None:
        from google import genai
        _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _client


def _call(prompt, config, retries=3):
    for attempt in range(retries):
        try:
            return _get_client().models.generate_content(model=MODEL, contents=prompt, config=config)
        except Exception as e:  # quá tải, mạng lỗi... thử lại
            if attempt == retries - 1:
                raise
            print(f"  (Lỗi gọi Gemini: {e} - thử lại sau 5 giây)")
            time.sleep(5)


def ask_text(prompt, temperature=0.8, fake="[GIẢ] Dạ... em chưa hiểu lắm ạ."):
    if FAKE:
        return fake
    from google.genai import types
    resp = _call(prompt, types.GenerateContentConfig(temperature=temperature))
    return resp.text.strip()


def ask_json(prompt, schema, temperature=0.2, fake=None):
    if FAKE:
        return schema.model_validate(fake)
    from google.genai import types
    config = types.GenerateContentConfig(
        temperature=temperature,
        response_mime_type="application/json",
        response_schema=schema,
    )
    resp = _call(prompt, config)
    return resp.parsed if resp.parsed is not None else schema.model_validate_json(resp.text)
