"""API de Muuk: AG-UI (transporte oficial) + A2UI v0.9 + acciones de regreso.

Rutas:
  POST /chat    → SSE con eventos AG-UI; la superficie llega como
                  ACTIVITY_SNAPSHOT (a2ui-surface) con ops v0.9
                  (createSurface/updateComponents/updateDataModel).
  POST /action  → interacción del usuario; cierra loop + memoria adaptativa.
"""

import json
import time
import uuid

from collections import defaultdict

import agent
import db
import a2ui_stream
from catalog import validar_componente
from ag_ui.encoder import EventEncoder
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from fastapi import UploadFile, File
#elevenLabs
import voice

from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Muuk API")

# Un único CORSMiddleware con todos los orígenes permitidos.
# (Tener más de uno causaba que las peticiones POST con preflight,
# como /login, fueran bloqueadas por el navegador en producción.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://godmuuk.tech",
        "https://www.godmuuk.tech",
    ],
    # Previews de Vercel (URLs por deploy, cambian siempre):
    # https://muuk-<hash>-<team>.vercel.app
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

_RATE_LIMIT = 10
_rate: dict[str, list[float]] = defaultdict(list)

# Usuario demo por defecto (Ana Torres, existe en la DB real).
DEFAULT_USER = "a1111111-0000-0000-0000-000000000001"


def _check_rate(ip: str):
    now = time.time()
    hits = [t for t in _rate[ip] if now - t < 60]
    if len(hits) >= _RATE_LIMIT:
        raise HTTPException(429, "rate limit")
    _rate[ip] = hits + [now]


class ChatRequest(BaseModel):
    session_id: str
    mensaje: str
    user_id: str = DEFAULT_USER


class ActionRequest(BaseModel):
    session_id: str
    componente: str
    evento: str
    payload: dict = {}
    user_id: str = DEFAULT_USER

class TTSRequest(BaseModel):
    text:str


class LoginRequest(BaseModel):
    nombre: str
    password: str


def _perfil_ui(user_id: str) -> dict:
    """Perfil de accesibilidad: adulto mayor → letra grande + lenguaje simple."""
    usuario = db.get_usuario(user_id) or {}
    edad = usuario.get("edad")
    senior = isinstance(edad, (int, float)) and edad >= 60
    return {"perfil": "senior" if senior else "estandar", "detalle": "simple" if senior else "extendido"}


def _limpiar_componentes(resp, user_id: str, session_id: str) -> list:
    """Validación fail-closed + dedupe + orden por preferencias del usuario.
    Igual que antes, pero ahora se aplica antes de construir las ops v0.9."""
    valid = []
    seen = set()
    for c in resp.componentes:
        if not validar_componente(c.type, c.props):
            db.registrar_interaccion(session_id, "SYSTEM_RESPONSE", f"ui_bloqueada:{c.type}")
            continue
        clave = c.type + json.dumps(c.props, sort_keys=True, default=str)
        if clave in seen:
            continue
        seen.add(clave)
        valid.append(c)
    preferred = [p["componente_nombre"] for p in db.get_preferencias(user_id) if p.get("componente_nombre")]
    pos = {c: i for i, c in enumerate(preferred)}
    valid.sort(key=lambda c: pos.get(c.type, len(pos)))
    return valid


def _run_agent(session_id: str, mensaje: str, user_id: str) -> list:
    historial = db.get_resumen_interacciones(session_id)
    perfil = _perfil_ui(user_id)

    prompt = (
        f"CONTEXTO DE SESIÓN:\n"
        f"user_id={user_id}\n"
        f"session_id={session_id}\n"
        f"perfil_ui={perfil['perfil']} (detalle={perfil['detalle']})\n"
        f"HISTORIAL: {json.dumps(historial, default=str)}\n\n"
        f"MENSAJE DEL USUARIO:\n"
        f"{mensaje}"
    )

    try:
        resp = agent.run_muuk(prompt)
    except agent._ModeloSaturado:
        return a2ui_stream.error_events(session_id,
            "El agente está ocupado justo ahora. Intenta de nuevo en unos segundos.")
    except Exception:
        # Fail-closed: sin datos de MCP no se responde con texto inventado.
        return a2ui_stream.error_events(session_id,
            "No pude conectar con tus datos. Intenta de nuevo en unos segundos.")

    # Fail-closed: solo componentes del catálogo sobreviven.
    resp.componentes = _limpiar_componentes(resp, user_id, session_id)
    return a2ui_stream.run_events(session_id, resp, perfil)


@app.post("/chat")
def chat(req: ChatRequest, request: Request):
    _check_rate(request.client.host if request.client else "demo")
    db.ensure_sesion(req.session_id, req.user_id)
    db.registrar_interaccion(req.session_id, "USER_MESSAGE", req.mensaje)
    events = _run_agent(req.session_id, req.mensaje, req.user_id)

    encoder = EventEncoder()

    def stream():
        for e in events:
            yield encoder.encode(e)

    return StreamingResponse(stream(), media_type=encoder.get_content_type())


@app.post("/action")
def action(req: ActionRequest, request: Request):
    _check_rate(request.client.host if request.client else "demo")
    db.ensure_sesion(req.session_id, req.user_id)
    db.registrar_interaccion(req.session_id, "UI_ACTION", f"{req.componente}:{req.evento}")

    # Única escritura de negocio; exige CTA explícito del usuario.
    if req.evento == "aplicar_plan":
        p = req.payload
        result = db.aplicar_plan(
            req.user_id,
            p.get("meses", 12),
            p.get("pago_mensual", 0),
            p.get("cat", 0),
            p.get("monto_original", 0),
        )
        return {"ok": True, "plan": result}

    if req.evento == "aceptar_reto":
        reto_id = req.payload.get("reto_id")

        if not reto_id:
            raise HTTPException(status_code=400, detail="reto_id requerido")

        result = db.validar_y_completar_reto(req.user_id, reto_id)

        return result

    return {"ok": True}


@app.get("/transacciones")
def transacciones(request: Request, user_id: str = DEFAULT_USER, limit: int = 20):
    """Detalle crudo para el frontend. Canal separado del LLM: el agente nunca
    ve estas filas. En producción: user_id derivado del token de sesión y rol
    de BD distinto al del agente (mcp_agent no tiene SELECT en transaccion)."""
    _check_rate(request.client.host if request.client else "demo")
    return db.get_transacciones(user_id, limit)

@app.post("/login")
def login(req: LoginRequest, request: Request):
    """Valida credenciales por usuario contra la BD (hash SHA-256)."""
    _check_rate(request.client.host if request.client else "demo")
    usuario = db.validar_login(req.nombre, req.password)
    if not usuario:
        raise HTTPException(401, "Usuario o contraseña incorrectos")
    return usuario

@app.post("/tts")
def tts(req: TTSRequest, request: Request):
    _check_rate(request.client.host if request.client else "demo")
    audio = voice.synthesize_speech(req.text)  # antes decía req.texto
    return StreamingResponse(iter([audio]), media_type="audio/mpeg")

@app.get("/muuk-coins")
def muuk_coins(request: Request, user_id: str = DEFAULT_USER):
    """Devuelve el saldo actual de Muuk Coins."""
    _check_rate(request.client.host if request.client else "demo")

    wallet = db.get_muuk_wallet(user_id)

    return {
        "user_id": user_id,
        "balance": wallet["muuk_coins"] if wallet else 0
    }


@app.get("/muuk-coins/history")
def muuk_coins_history(
    request: Request,
    user_id: str = DEFAULT_USER,
    limit: int = 20
):
    """Devuelve el historial de Muuk Coins."""
    _check_rate(request.client.host if request.client else "demo")

    wallet = db.get_muuk_wallet(user_id)
    history = db.get_muuk_coin_history(user_id, limit)

    return {
        "user_id": user_id,
        "balance": wallet["muuk_coins"] if wallet else 0,
        "history": history
    }


@app.get("/challenges")
def challenges(request: Request, user_id: str = DEFAULT_USER):
    """Devuelve los retos activos que el usuario aún no ha completado."""
    _check_rate(request.client.host if request.client else "demo")

    return {
        "user_id": user_id,
        "challenges": db.get_retos_disponibles(user_id)
    }


@app.post("/stt")
async def stt(request: Request, file: UploadFile = File(...)):
    _check_rate(request.client.host if request.client else "demo")
    audio_bytes = await file.read()
    texto = voice.transcribe_speech(audio_bytes)
    return {"text": texto}


@app.get("/perfil")
def perfil(request: Request, user_id: str = DEFAULT_USER):
    _check_rate(request.client.host if request.client else "demo")
    usuario = db.get_usuario(user_id)

    if not usuario:
        raise HTTPException(404, "usuario no encontrado")

    return {
        "usuario": usuario,
        "perfil_financiero": db.get_perfil_financiero(user_id),
        "productos": db.get_productos_usuario(user_id),
    }
