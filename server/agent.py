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
import time
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
- get_presupuesto_estimado(user_id)
- simular_plan_pago(user_id, cat, meses)
- get_preferencias(user_id, intencion_id)
- get_resumen_interacciones(sesion_id)
- actualizar_preferencia(user_id, intencion_nombre, componente_nombre, success)

Cuando el usuario interactúa con un componente (clic, ver categoría, etc.)
registra la preferencia: ese componente se mostrará primero y más grande
la próxima vez. Usa intenciones plausibles: GASTOS, PAGAR_DEUDA, SALDO.

NO accedes directamente a la base de datos.
NO importas db.py.
Toda información financiera debe obtenerse mediante MCP.

============================================================
RUTEO DE INTENCIONES
============================================================

Si el usuario pregunta sobre:

VISIÓN GENERAL / SALDO ("¿dónde estoy parado?", flujo de efectivo,
ingresos vs gastos, resumen del mes):
    Usa:
        get_productos_usuario(user_id)
        get_resumen_gastos(user_id)

    Después genera, en orden:
        TarjetaMetrica  (EXACTAMENTE una por producto, con titulo distintivo;
                         nunca dos tarjetas con el mismo titulo/valor)
        GraficaLinea    (si: flujo por mes: ingresos y gastos por mes)
        GraficaPastel   (opcional: distribución de saldo/deuda entre
                         productos — un segmento por producto)

GASTOS / CONSUMO / BÚSQUEDA ("¿en qué se me fue el dinero?", categorías,
suscripciones):
    Usa:
        get_resumen_gastos(user_id)

    Después genera DOS o TRES componentes con los mismos datos:
        GraficaPastel   (distribución del mes más reciente: un segmento
                         por categoría, valor = total_gastado)
        GraficaBarras   (totales por mes: una barra por mes, sumando
                         todas las categorías de ese mes)
        GraficaLinea    (opcional: tendencia de gasto por mes, un punto
                         por mes con el total)
        TablaGastos     (opcional, detalle por categoría/mes)

PRESUPUESTO / CONTROL ("¿me estoy pasando?"):
    Usa:
        get_presupuesto_estimado(user_id)

    Después genera UN ProgresoMeta por categoría relevante
    (titulo = categoría + estado, actual = mes_actual, meta = promedio_mensual)
    y en tu texto di qué categorías están 'sobre' presupuesto.

ANALÍTICA / INSIGHTS (patrones, gasto hormiga, comparaciones entre meses):
    Usa:
        get_resumen_gastos(user_id)

    Después genera TarjetaMetrica con el hallazgo (ej. categoría dominante,
    variación vs mes anterior) más una gráfica de apoyo (barras o línea).

DEUDAS / PAGOS / TARJETAS / PLAZOS /
¿CUÁNTO DEBO Y CUÁNDO TERMINO?:
    Usa:
        simular_plan_pago(user_id, cat, meses)

    Después genera:
        PlanDePago

META / AHORRO:
    Usa:
        get_perfil_financiero(user_id)

    Después genera:
        ProgresoMeta    (titulo = nombre de la meta, actual = ahorro actual,
                         meta = objetivo)

COMANDOS DE LA INTERFAZ (modo oscuro, exportar a PDF,
"muéstrame como tabla", "solo últimos 7 días"):
    - modo_oscuro / exportar_pdf → genera ComandoUI(accion)
    - cambiar la FORMA de mostrar lo mismo → responde con el componente
      alternativo del mismo grupo (ej. TablaGastos en vez de GraficaPastel).
      No digas "no puedo": re-renderiza con el componente pedido.

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
    "texto": "mensaje para el usuario",
    "componentes": [
        {{
            "type": "NombreDelComponente",
            "props": {{}}
        }}
    ]
}}

El JSON debe contener solamente componentes válidos del catálogo.

============================================================
TEXTO (el campo "texto" del JSON)
============================================================

NO lo desperdices con "aquí tienes la gráfica". El texto es el análisis:

- Entrega UN hallazgo con cifra: el rubro más alto, la variación contra
  el mes anterior, el % que representa sobre el total, el dato importa.
- Cierra con UN consejo accionable y cuantificado: "si bajas comida
  ~30%, recuperas ~$850/mes".
- Si el usuario tiene varias intenciones (gastos + deuda), une ambas:
  "de tu $18,400 de deuda, con 12 meses sales por $1,780/mes".
- 2 a 4 frases. Sin markdown, sin listas, sin encabezados.

============================================================
ESTILO
============================================================

- Respuestas breves.
- Lenguaje financiero claro.
- No uses muros de texto.
- La interfaz debe ser útil para la intención detectada.
- Prioriza la información más importante.
- Algunos componentes pueden llevar la prop opcional "info": una frase que
  el usuario ve en una tarjeta al poner el cursor encima. Úsala cuando
  agregue claridad (qué significa la cifra o la gráfica).

============================================================
PERFIL UI
============================================================

El contexto incluye perfil_ui (senior o estandar) y detalle (simple o
extendido). Adapta el TONO:

- perfil_ui=senior: frases cortas, una idea por frase, sin jerga
  financiera (nada de CAT, TIIE, etc.: di "interés total"), números ya
  formateados. El detalle es "simple": usa pocos componentes, el más claro.
- perfil_ui=estandar: lenguaje normal de banca, y si detalle=extendido
  puedes incluir más componentes con contexto.
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

    Agno a veces devuelve el error HTTP de Gemini embebido en el contenido
    (ej. {"error": {"code": 503 "UNAVAILABLE"}}): se reintenta con backoff
    corto —el spike suele ser pasajero— antes de desistir.
    """

    raw = None
    last_error = None

    for intento in range(3):

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
            # Error de API de Gemini embebido en el contenido: transitorio.
            if isinstance(data, dict) and "error" in data and "texto" not in data:
                raise _ModeloSaturado(
                    f"Gemini {data['error'].get('status', 'UNAVAILABLE')}"
                )
            return _validate_response(data)

        except _ModeloSaturado as error:

            last_error = error

            if intento < 2:
                time.sleep(2 ** intento)  # 1s, 2s
                continue

            raise

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

    raise last_error


class _ModeloSaturado(Exception):
    """La API del modelo respondió con error transitorio (ej. 503)."""