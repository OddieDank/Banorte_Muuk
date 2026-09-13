"""
Muuk — Agente A2UI sobre MCP.

Flujo:

    Usuario
       ↓
    Gemini
       ↓
    MCP Tool
       ↓
    TigerData
       ↓
    Gemini
       ↓
    JSON A2UI
       ↓
    api.py

El agente NO consulta db.py directamente.
Toda la información financiera pasa por MCP.
"""

import asyncio
import json
import os
import sys
import threading
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.mcp import MCPTools
from pydantic import BaseModel

from catalog import CATALOG, validar_componente


# ============================================================
# MODELOS DE SALIDA
# ============================================================

class Componente(BaseModel):
    type: str
    props: dict


class MuukResponse(BaseModel):
    texto: str
    componentes: list[Componente]


# ============================================================
# CATÁLOGO PARA GEMINI
# ============================================================

SCHEMAS = json.dumps(
    {
        nombre: schema.model_json_schema()
        for nombre, schema in CATALOG.items()
    },
    ensure_ascii=False,
    indent=2,
)


# ============================================================
# INSTRUCCIONES DEL AGENTE
# ============================================================

INSTRUCTIONS = f"""
Eres Muuk, un asistente financiero que genera interfaces dinámicas
para una aplicación bancaria.

Tu trabajo tiene DOS etapas:

1. Entender la intención del usuario y obtener la información necesaria
   utilizando las herramientas MCP disponibles.

2. Utilizar el resultado de MCP para generar una interfaz A2UI.

============================================================
HERRAMIENTAS MCP
============================================================

Puedes utilizar estas herramientas:

- get_usuario(user_id)
- get_perfil_financiero(user_id)
- get_productos_usuario(user_id)
- get_resumen_gastos(user_id, meses)
- simular_plan_pago(user_id, cat, meses)
- get_preferencias(user_id, intencion_id)
- get_resumen_interacciones(sesion_id)

NO accedes directamente a la base de datos.
NO importas db.py.
Toda información financiera debe obtenerse mediante MCP.

============================================================
RUTEO DE INTENCIONES
============================================================

Si el usuario pregunta sobre:

GASTOS / CONSUMO:
    Usa:
        get_resumen_gastos(user_id)

    Después genera DOS o TRES componentes con los mismos datos:
        GraficaPastel   (distribución del mes más reciente: un segmento
                         por categoría, valor = total_gastado)
        GraficaBarras   (totales por mes: una barra por mes, sumando
                         todas las categorías de ese mes)
        TablaGastos     (opcional, detalle por categoría/mes)

DEUDAS / PAGOS / TARJETAS / PLAZOS:
    Usa:
        simular_plan_pago(user_id, cat, meses)

    Después genera:
        PlanDePago

SALDO / CUENTAS / PRODUCTOS:
    Usa:
        get_productos_usuario(user_id)

    Después genera:
        TarjetaMetrica  (una por producto: titulo = nombre del producto,
                         valor = saldo o deuda formateado, ej "$8,500",
                         subtitulo = "saldo" o "deuda")

Si necesitas contexto adicional para personalizar la respuesta,
puedes usar:

    get_usuario(user_id)
    get_perfil_financiero(user_id)
    get_preferencias(user_id)
    get_resumen_interacciones(sesion_id)

============================================================
REGLAS DE DATOS
============================================================

- NUNCA inventes cifras financieras.
- Si una cifra viene de MCP, utiliza exactamente esa cifra.
- Si MCP devuelve un error, no inventes una respuesta.
- No solicites ni utilices transacciones crudas.
- Los datos detallados de transacciones NO forman parte del contexto
  del agente.
- Para gastos utiliza solamente los agregados proporcionados por MCP.

============================================================
REGLAS A2UI
============================================================

Componentes disponibles:

{SCHEMAS}

Solo puedes utilizar componentes definidos en este catálogo.

No inventes nuevos component types.

Las props deben respetar exactamente el esquema de cada componente.

============================================================
PLAN DE PAGO
============================================================

Si el usuario quiere pagar una deuda:

1. Determina el número de meses solicitado (default 12) y una CAT base
   razonable para tarjeta de crédito en México (típico 30-45).
2. Llama a:

    simular_plan_pago(user_id, cat, meses)

3. MCP devuelve:

    monto_original  (la deuda real del usuario)
    opciones        (varias simulaciones con meses, pago_mensual, cat, total)

4. Genera PlanDePago copiando EXACTAMENTE monto_original y TODAS las
   opciones devueltas por MCP. El mensaje debe mencionar el monto a
   reestructurar, ej: "Reestructura tu saldo de $18,400".

NUNCA calcules manualmente un pago que MCP ya puede calcular.

NUNCA inventes:
- deuda
- pago mensual
- CAT
- total

============================================================
SALIDA
============================================================

Tu respuesta FINAL debe ser exclusivamente JSON válido.

NO uses Markdown.
NO uses ```json.
NO agregues explicaciones fuera del JSON.

Formato obligatorio:

{{
    "texto": "mensaje corto para el usuario",
    "componentes": [
        {{
            "type": "NombreDelComponente",
            "props": {{}}
        }}
    ]
}}

El JSON debe contener solamente componentes válidos del catálogo.

============================================================
ESTILO
============================================================

- Respuestas breves.
- Lenguaje financiero claro.
- No uses muros de texto.
- La interfaz debe ser útil para la intención detectada.
- Prioriza la información más importante.
"""


# ============================================================
# MCP + AGENTE
# ============================================================

def build_agent(mcp_command: list[str] | None = None) -> Agent:

    command = mcp_command or [
        sys.executable,
        str(Path(__file__).parent / "mcp_server.py"),
    ]

    return Agent(
        name="Muuk",
        model=Gemini(
            id=os.getenv(
                "GEMINI_MODEL",
                "gemini-2.5-flash",
            ),
            api_key=os.getenv("GEMINI_API_KEY"),
        ),
        tools=[
            MCPTools(
                command=" ".join(command)
            )
        ],
        instructions=INSTRUCTIONS,
        markdown=False,
    )


# ============================================================
# CONEXIÓN PERSISTENTE
# ============================================================

_LOOP = asyncio.new_event_loop()
_LOCK = threading.Lock()

_AGENT: Agent | None = None


def _get_agent() -> Agent:

    global _AGENT

    if _AGENT is None:

        _AGENT = build_agent()

        _LOOP.run_until_complete(
            _AGENT.tools[0].connect()
        )

    return _AGENT


# ============================================================
# PARSEO Y VALIDACIÓN
# ============================================================

def _extract_json(raw: str) -> dict:

    """
    Extrae el objeto JSON aunque Gemini haya agregado accidentalmente
    algún texto antes o después.
    """

    start = raw.find("{")
    end = raw.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError("Gemini no devolvió JSON")

    return json.loads(
        raw[start:end + 1],
        strict=False,
    )


def _validate_response(data: dict) -> MuukResponse:

    """
    Valida:

    1. estructura MuukResponse
    2. componentes existentes
    3. props contra catálogo
    """

    response = MuukResponse.model_validate(data)

    valid_components = []

    for component in response.componentes:

        if not validar_componente(
            component.type,
            component.props,
        ):
            raise ValueError(
                f"Componente A2UI inválido: "
                f"{component.type}"
            )

        valid_components.append(component)

    response.componentes = valid_components

    return response


# ============================================================
# FUNCIÓN PRINCIPAL DEL AGENTE
# ============================================================

def run_muuk(
    prompt: str,
    mcp_command: list[str] | None = None,
) -> MuukResponse:

    """
    Ejecuta:

        prompt
          ↓
        Gemini
          ↓
        MCP
          ↓
        Gemini
          ↓
        JSON A2UI

    No consulta db.py directamente.
    """

    with _LOCK:

        agent = _get_agent()

        result = _LOOP.run_until_complete(
            agent.arun(prompt)
        )

    raw = result.content

    if not isinstance(raw, str):
        raw = (
            getattr(raw, "text", None)
            or str(raw)
        )

    try:

        data = _extract_json(raw)

        response = _validate_response(data)

        return response

    except Exception as error:

        print(
            "[run_muuk] Error procesando respuesta:",
            type(error).__name__,
            error,
        )

        print(
            "[run_muuk] Respuesta recibida:",
            raw[:1000],
        )

        raise ValueError(
            "El agente no produjo un JSON A2UI válido"
        ) from error