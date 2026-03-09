import os
from openai import OpenAI

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
#OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "") # old version, sometimes work sometimes doesn't in some environments.

MODEL = "openai/gpt-oss-120b:free"  # darmowy model (DeepSeek wycofywany)

# Direct initalization of the client (not recommended for production due to potential issues with multiple instances)
# client = OpenAI(
#     base_url= "https://openrouter.ai/api/v1",
#     api_key=OPENROUTER_API_KEY
# )

_client = None # globalna zmienna do przechowywania instancji klienta

def _get_client(): # inicjalizacja klienta tylko raz
    global _client # używamy globalnej zmiennej do przechowywania instancji klienta
    if _client is None: # jeśli klient nie został jeszcze utworzony, tworzymy go
        _client = OpenAI( # inicjalizacja klienta z kluczem API i adresem bazowym
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY
        )
    return _client # zwracamy instancję klienta, która jest teraz przechowywana w globalnej zmiennej

def ask_openrouter(prompt: str) -> str:
    if not OPENROUTER_API_KEY:
        return "Brak OPENROUTER_API_KEY"
    try:
        client = _get_client()  # inicjalizacja klienta tylko raz
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            extra_body={"reasoning": {"enabled": True}}
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Błąd API: {e}"