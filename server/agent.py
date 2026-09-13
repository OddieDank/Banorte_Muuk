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
- simular_plan_pago(user_id, meses, cat)
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

    Después genera:
        TablaGastos

DEUDAS / PAGOS / TARJETAS / PLAZOS:
    Usa:
        simular_plan_pago(user_id, meses, cat)

    Después genera:
        PlanDePago

SALDO / CUENTAS / PRODUCTOS:
    Usa:
        get_productos_usuario(user_id)

    Después genera:
        TablaGastos

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

1. Determina el número de meses solicitado.
2. Si el usuario no especifica meses, utiliza una opción razonable.
3. Determina una CAT válida.
4. Llama a:

    simular_plan_pago(user_id, meses, cat)

5. Utiliza exactamente los valores devueltos por MCP:

    meses
    pago_mensual
    cat
    total

6. Genera PlanDePago.

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
        "python",
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