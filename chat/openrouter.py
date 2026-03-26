import base64
import mimetypes
import hashlib
import json

from django.conf import settings
from openai import OpenAI
from openai import AuthenticationError
from openai import NotFoundError
from django.core.cache import cache

OPENROUTER_API_KEY = settings.OPENROUTER_API_KEY

TEXT_MODEL = settings.OPENROUTER_MODEL_TEXT
MULTIMODAL_MODEL = settings.OPENROUTER_MODEL_MULTIMODAL 

_client = None


def _normalize_api_key(raw_key: str) -> str:
    if not raw_key:
        return ""
    key = raw_key.strip()
    if key.lower().startswith("bearer "):
        key = key[7:].strip()
    return key


def _get_client():
    global _client
    if _client is None:
        _client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=_normalize_api_key(OPENROUTER_API_KEY),
        )
    return _client


def _payload_has_non_text_input(payload) -> bool:
    return any(part.get("type") != "text" for part in payload)


def _select_model(payload) -> str:
    if _payload_has_non_text_input(payload):
        return MULTIMODAL_MODEL
    return TEXT_MODEL


def build_user_content(message_obj):
    content = [{"type": "text", "text": message_obj.content}]

    for att in message_obj.attachments.all():
        file_path = att.file.path
        mime, _ = mimetypes.guess_type(file_path)
        mime = mime or "application/octet-stream"

        with open(file_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")

        if att.file_type == "img":
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{b64}"},
                }
            )
        else:
            content.append(
                {
                    "type": "file",
                    "file": {
                        "filename": att.file.name.split("/")[-1],
                        "file_data": f"data:{mime};base64,{b64}",
                    },
                }
            )

    return content


def ask_openrouter(message_obj) -> str:
    payload = build_user_content(message_obj)
    model = _select_model(payload)
    payload_str = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    key = f"ai:{model}:{hashlib.sha256(payload_str.encode('utf-8')).hexdigest()}"

    cached = cache.get(key)
    if cached:
        return cached

    normalized_key = _normalize_api_key(OPENROUTER_API_KEY)
    if not normalized_key:
        return "Brak OPENROUTER_API_KEY"

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": payload}],
            extra_body={"reasoning": {"enabled": True}},
        )
        answer = response.choices[0].message.content
        cache.set(key, answer, timeout=600)
        return answer
    except NotFoundError as e:
        msg = str(e)
        if "No endpoints found that support image input" in msg:
            return (
                "Blad API (404): wybrany model nie obsluguje zalacznikow obrazu/pliku. "
                "Ustaw OPENROUTER_MODEL_MULTIMODAL w .env na model multimodalny."
            )
        return f"Blad API: {e}"
    except AuthenticationError:
        return (
            "Blad API (401): OpenRouter odrzucil klucz. "
            "Sprawdz OPENROUTER_API_KEY w .env (wklej sam klucz, bez 'Bearer '), "
            "czy klucz jest aktywny i nalezy do poprawnego konta OpenRouter."
        )
    except Exception as e:
        return f"Blad API: {e}"
