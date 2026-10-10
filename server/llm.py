"""
Goi Gemini - gom vao 1 cho (ported tu prototype/llm.py)
- ask_text: tra ve van ban (dung cho hoc sinh ao)
- ask_json: tra ve JSON theo schema Pydantic (dung cho phan loai, cham diem)
Che do thu khong can API key: dat bien moi truong FAKE_LLM=1
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

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
FAKE = os.getenv("FAKE_LLM") == "1"
PROMPT_DIR = Path(__file__).parent / "prompts"
_client = None


def load_prompt(name, **values):
    """Doc prompts/<name>.md va thay cac bien $ten_bien bang gia tri."""
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
        except Exception as e:  # qua tai, mang loi... thu lai
            if attempt == retries - 1:
                raise
            print(f"  (Loi goi Gemini: {e} - thu lai sau 5 giay)")
            time.sleep(5)


def ask_text(prompt, temperature=0.8, fake="[GIẢ] Dạ... em chưa hiểu lắm ạ."):
    if FAKE:
        return fake
    from google.genai import types
    resp = _call(prompt, types.GenerateContentConfig(
        temperature=temperature,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),  # tắt cảnh báo AFC
    ))
    return resp.text.strip()


def ask_json(prompt, schema, temperature=0.2, fake=None):
    if FAKE:
        return schema.model_validate(fake)
    from google.genai import types
    config = types.GenerateContentConfig(
        temperature=temperature,
        response_mime_type="application/json",
        response_schema=schema,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),  # tat canh bao AFC
    )
    resp = _call(prompt, config)
    return resp.parsed if resp.parsed is not None else schema.model_validate_json(resp.text)
