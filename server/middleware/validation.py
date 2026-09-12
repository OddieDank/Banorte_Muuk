"""
Validaciones de Muuk.

Responsabilidades:
- Validar entradas del usuario antes de procesarlas.
- Validar intenciones conocidas.
- Validar parámetros básicos de operaciones financieras.
- Proporcionar validaciones generales independientes del catálogo A2UI.

La validación específica de componentes A2UI permanece en
validate_a2ui.py / catalog.py.
"""

import re


# ============================================================
# INTENCIONES
# ============================================================

VALID_INTENTS = {
    "spending_analysis",
    "payment_plan",
    "payment_confirmation",
    "profile",
    "products",
    "general_finance",
}


# ============================================================
# PROMPT
# ============================================================

MAX_PROMPT_LENGTH = 2000


def validate_prompt(prompt: str) -> tuple[bool, str]:
    """
    Valida el mensaje recibido del usuario.

    No intenta determinar la intención financiera.
    Esa responsabilidad corresponde al agente/LLM.
    """

    if not isinstance(prompt, str):
        return False, "El mensaje debe ser texto."

    prompt = prompt.strip()

    if not prompt:
        return False, "El mensaje no puede estar vacío."

    if len(prompt) > MAX_PROMPT_LENGTH:
        return False, "El mensaje es demasiado largo."

    return True, ""


# ============================================================
# INTENT
# ============================================================

def validate_intent(intent: str) -> tuple[bool, str]:
    """
    Verifica que una intención identificada por el agente
    pertenezca al conjunto permitido.
    """

    if not isinstance(intent, str):
        return False, "La intención debe ser texto."

    normalized = intent.strip().lower()

    if normalized not in VALID_INTENTS:
        return False, f"Intención no permitida: {normalized}"

    return True, ""


# ============================================================
# USER ID
# ============================================================

def validate_user_id(user_id: str) -> tuple[bool, str]:
    """
    Validación básica del identificador de usuario.

    No determina si el usuario existe.
    """

    if not isinstance(user_id, str):
        return False, "user_id debe ser texto."

    user_id = user_id.strip()

    if not user_id:
        return False, "user_id no puede estar vacío."

    # UUID o identificadores sencillos como u1/u2 para el
    # entorno actual del prototipo.
    if not re.fullmatch(
        r"[A-Za-z0-9_-]{1,128}",
        user_id,
    ):
        return False, "Formato de user_id inválido."

    return True, ""


# ============================================================
# FINANCIAL VALUES
# ============================================================

def validate_amount(
    amount: float,
    minimum: float = 0.01,
    maximum: float = 10_000_000,
) -> tuple[bool, str]:
    """
    Valida un monto financiero genérico.
    """

    try:
        value = float(amount)
    except (TypeError, ValueError):
        return False, "El monto debe ser numérico."

    if value < minimum:
        return False, "El monto debe ser mayor que cero."

    if value > maximum:
        return False, "El monto excede el límite permitido."

    return True, ""


def validate_months(
    months: int,
    minimum: int = 1,
    maximum: int = 360,
) -> tuple[bool, str]:
    """
    Valida el número de meses de un plan.
    """

    if not isinstance(months, int):
        return False, "Los meses deben ser un entero."

    if months < minimum or months > maximum:
        return False, (
            f"Los meses deben estar entre "
            f"{minimum} y {maximum}."
        )

    return True, ""


# ============================================================
# PAYMENT PLAN
# ============================================================

def validate_payment_plan(
    months: int,
    monthly_payment: float,
    cat: float,
) -> tuple[bool, str]:
    """
    Validación básica de los parámetros de un plan de pago.
    """

    ok, error = validate_months(months)

    if not ok:
        return False, error

    ok, error = validate_amount(monthly_payment)

    if not ok:
        return False, error

    try:
        cat_value = float(cat)
    except (TypeError, ValueError):
        return False, "CAT debe ser numérico."

    if cat_value <= 0 or cat_value > 1000:
        return False, "CAT fuera de rango permitido."

    return True, ""


# ============================================================
# GENERIC REQUEST VALIDATION
# ============================================================

def validate_request(
    prompt: str,
    user_id: str,
) -> tuple[bool, str]:
    """
    Ejecuta las validaciones básicas de una solicitud.
    """

    ok, error = validate_user_id(user_id)

    if not ok:
        return False, error

    ok, error = validate_prompt(prompt)

    if not ok:
        return False, error

    return True, ""