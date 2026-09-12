"""
Planificador de UI de Muuk.

Responsabilidades:
- Traducir una intención financiera a una selección de componentes UI.
- Aplicar reglas de presentación consistentes.
- Mantener separada la lógica de negocio de la selección visual.

Este módulo NO:
- Consulta la base de datos.
- Ejecuta acciones financieras.
- Renderiza HTML.
- Genera directamente mensajes A2UI.

El resultado se entrega al agente/API para ser validado contra
el catálogo de componentes.
"""

from dataclasses import dataclass


# ============================================================
# UI PLAN
# ============================================================

@dataclass
class UIPlan:
    """
    Plan de interfaz generado a partir de una intención.
    """

    components: list[str]
    priority: list[str]
    reason: str


# ============================================================
# INTENT → UI
# ============================================================

UI_RULES: dict[str, UIPlan] = {

    # --------------------------------------------------------
    # Gastos
    # --------------------------------------------------------

    "spending_analysis": UIPlan(
        components=[
            "TablaGastos",
        ],
        priority=[
            "TablaGastos",
        ],
        reason="El usuario necesita visualizar sus gastos.",
    ),

    # --------------------------------------------------------
    # Plan de pago
    # --------------------------------------------------------

    "payment_plan": UIPlan(
        components=[
            "PlanDePago",
        ],
        priority=[
            "PlanDePago",
        ],
        reason="El usuario solicita opciones para una deuda.",
    ),

    # --------------------------------------------------------
    # Confirmación
    # --------------------------------------------------------

    "payment_confirmation": UIPlan(
        components=[
            "Confirmacion",
        ],
        priority=[
            "Confirmacion",
        ],
        reason="La operación requiere confirmación explícita.",
    ),

}


# ============================================================
# DEFAULT
# ============================================================

DEFAULT_PLAN = UIPlan(
    components=[
        "Confirmacion",
    ],
    priority=[
        "Confirmacion",
    ],
    reason="No se identificó una interfaz financiera especializada.",
)


# ============================================================
# PLANNER
# ============================================================

def plan_ui(intent: str) -> UIPlan:
    """
    Devuelve el plan de UI correspondiente a una intención.

    Si la intención no está definida, utiliza DEFAULT_PLAN.
    """

    normalized_intent = intent.strip().lower()

    return UI_RULES.get(
        normalized_intent,
        DEFAULT_PLAN,
    )


# ============================================================
# COMPONENT PRIORITY
# ============================================================

def prioritize_components(
    components: list[str],
    preferred_components: list[str] | None = None,
) -> list[str]:
    """
    Ordena componentes considerando las preferencias del usuario.

    preferred_components puede provenir de las preferencias
    almacenadas por Muuk.
    """

    if not preferred_components:
        return components

    preferred = {
        component: index
        for index, component in enumerate(preferred_components)
    }

    return sorted(
        components,
        key=lambda component: preferred.get(
            component,
            len(preferred),
        ),
    )


# ============================================================
# CATALOG CHECK
# ============================================================

def filter_catalog_components(
    components: list[str],
    catalog: list[str],
) -> list[str]:
    """
    Elimina componentes que no existen en el catálogo permitido.

    Esto es una segunda capa de protección.
    La validación de props continúa siendo responsabilidad de
    catalog.py.
    """

    allowed = set(catalog)

    return [
        component
        for component in components
        if component in allowed
    ]