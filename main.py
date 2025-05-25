from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import json
import re
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

class SuggestRequest(BaseModel):
    title: str
    primaryGenre: str
    additionalGenres: list[str] | None = None
    userPrompt: str
    currentContent: str
    isChapterBased: bool
    previousChapter: str | None = None
    previousBook: str | None = None

def _smart_excerpt(text: str, segment_length: int = 1500) -> str:
    if len(text) <= segment_length:
        return text
    idx = text.rfind('.', 0, segment_length)
    if idx < 0:
        idx = text.rfind('\n', 0, segment_length)
    if idx < 0:
        idx = segment_length
    return text[:idx + 1]

def _clean_response(raw: str, previous_text: str = "") -> str:
    allowed_special = r'\*#_>\-'
    pattern = rf'[^\w\sÁÉÍÓÚÑáéíóúñ.,;:!¿\?¡()"—\n{allowed_special}]'
    sanitized = re.sub(pattern, '', raw, flags=re.UNICODE).strip()
    sanitized = re.sub(r'^[^\w\sÁÉÍÓÚÑáéíóúñ*#_>]+', '', sanitized, flags=re.UNICODE)

    if previous_text:
        previous_clean = re.sub(r'\s+', ' ', previous_text.lower().strip())
        current_clean = re.sub(r'\s+', ' ', sanitized.lower().strip())
        overlap_index = current_clean.find(previous_clean[-200:])
        if overlap_index >= 0:
            sanitized = sanitized[overlap_index + len(previous_clean[-200:]):].lstrip()

    lines = sanitized.split('\n')
    filtered = []
    seen = set()
    for line in lines:
        t = line.strip()
        if not t or t in seen:
            continue
        seen.add(t)
        letters = len(re.findall(r'[A-Za-zÁÉÍÓÚÑáéíóúñ]', t))
        if letters / max(len(t), 1) > 0.6:
            filtered.append(t)

    result = "\n".join(filtered).strip()
    while "\n\n\n" in result:
        result = result.replace("\n\n\n", "\n\n")

    if previous_text:
        last_char = previous_text.rstrip()[-1:]
        if last_char not in ".!?":
            result = result[0].lower() + result[1:] if result else ""
        else:
            result = result[0].upper() + result[1:] if result else ""
        if not previous_text.endswith((' ', '\n')) and not result.startswith((' ', '\n')):
            result = " " + result

    return result.strip()

def build_prompt(req: SuggestRequest) -> str:
    safe = _smart_excerpt(req.currentContent)
    ctx = ""
    if req.isChapterBased and req.previousChapter:
        ctx = "\n\nContexto previo del capítulo:\n" + _smart_excerpt(req.previousChapter)
    elif not req.isChapterBased and req.previousBook:
        ctx = "\n\nContexto adicional del libro previo:\n" + _smart_excerpt(req.previousBook)

    instructions = """
Eres un escritor profesional de narrativa en español. Tu tarea es continuar el texto de forma coherente y fluida, comenzando directamente desde el punto en que se dejó el texto previo. No incluyas ningún texto de relleno, caracteres extraños o contenido sin sentido al inicio. La continuación debe ser natural y parecer escrita por un autor humano.

Prohibido:
- Comenzar con texto incoherente, símbolos o caracteres extraños.
- Repetir frases o fragmentos del texto previo.
- Incluir encabezados, comentarios, resúmenes o meta-instrucciones.
- Usar símbolos extraños, contenido sin sentido o mezcla de idiomas.
- Romper la narrativa con cortes abruptos o preguntas al lector.

Debe:
- Continuar directamente desde el texto anterior sin repetir nada.
- Usar gramática clara, puntuación correcta y lenguaje natural.
- Parecer escrito por una persona real, con fluidez y creatividad.
- Usar Markdown de manera adecuada según el tipo de contenido:
  - En ficción: *cursiva* para pensamientos, **negrita** para énfasis, > junto a las comillas ("") para diálogos o citas, en las citas recuerda añadir correctamente al autor.
  - En artículos o ensayos: párrafos claros, evita adornos innecesarios.
  - En blogs o tutoriales: puedes usar viñetas, claridad paso a paso.
  - En investigaciones: lenguaje formal, directo, sin opiniones.

Solo genera el siguiente fragmento de la historia, comenzando de manera coherente y sin texto de relleno.
"""

    return f"Texto previo:\n{safe}{ctx}\n\n{instructions}"

@app.post("/suggest")
async def suggest(req: SuggestRequest):
    prompt = build_prompt(req)
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise HTTPException(500, detail="API Key de DeepSeek no configurada")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    body = {
        "model": DEEPSEEK_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "top_p": 0.95,
        "max_tokens": 2048,
        "stream": False,
    }

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            response = await client.post(DEEPSEEK_URL, headers=headers, json=body)

        if response.status_code != 200:
            raise HTTPException(response.status_code, detail=f"Error de DeepSeek: {response.text}")

        result = response.json()
        content = result["choices"][0]["message"]["content"]
        cleaned = _clean_response(content or "", previous_text=req.currentContent)

        return {"suggestion": cleaned.strip()}

    except httpx.ReadTimeout:
        raise HTTPException(status_code=504, detail="DeepSeek no respondió a tiempo")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
