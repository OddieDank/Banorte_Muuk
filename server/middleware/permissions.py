"""
Control de permisos de Muuk.

Responsabilidades:
- Definir las capacidades disponibles en el sistema.
- Determinar si un usuario puede ejecutar una acción.
- Mantener separada la autenticación (auth.py) de la autorización.

Este módulo NO autentica usuarios y NO accede directamente a la base de datos.
"""

from enum import Enum


# ============================================================
# PERMISSIONS
# ============================================================

class Permission(str, Enum):
    """
    Capacidades que pueden existir dentro de Muuk.
    """

    VIEW_PROFILE = "view_profile"
    VIEW_PRODUCTS = "view_products"
    VIEW_SPENDING_SUMMARY = "view_spending_summary"
    VIEW_TRANSACTIONS = "view_transactions"

    SIMULATE_PAYMENT_PLAN = "simulate_payment_plan"

    APPLY_PAYMENT_PLAN = "apply_payment_plan"

    VIEW_UI_PREFERENCES = "view_ui_preferences"
    UPDATE_UI_PREFERENCES = "update_ui_preferences"


# ============================================================
# DEFAULT USER PERMISSIONS
# ============================================================

DEFAULT_PERMISSIONS = {
    Permission.VIEW_PROFILE,
    Permission.VIEW_PRODUCTS,
    Permission.VIEW_SPENDING_SUMMARY,
    Permission.VIEW_TRANSACTIONS,
    Permission.SIMULATE_PAYMENT_PLAN,
    Permission.VIEW_UI_PREFERENCES,
    Permission.UPDATE_UI_PREFERENCES,
}


# ============================================================
# RESTRICTED PERMISSIONS
# ============================================================

# Acciones que implican modificar información financiera.
#
# Tener el permiso NO significa que la acción pueda ejecutarse
# automáticamente: la acción también requiere confirmación
# explícita del usuario.

SENSITIVE_PERMISSIONS = {
    Permission.APPLY_PAYMENT_PLAN,
}


# ============================================================
# PERMISSION CHECK
# ============================================================

def has_permission(
    user_id: str,
    permission: Permission,
) -> bool:
    """
    Determina si un usuario posee un permiso.

    Para el prototipo, todos los usuarios autenticados tienen
    los permisos normales definidos en DEFAULT_PERMISSIONS.

    Las acciones sensibles se manejan por separado.
    """

    if not user_id:
        return False

    return permission in DEFAULT_PERMISSIONS


def require_permission(
    user_id: str,
    permission: Permission,
) -> None:
    """
    Valida que el usuario tenga un permiso.

    Lanza PermissionError si el permiso no está disponible.
    """

    if not has_permission(user_id, permission):
        raise PermissionError(
            f"User '{user_id}' does not have permission "
            f"'{permission.value}'."
        )


# ============================================================
# SENSITIVE ACTIONS
# ============================================================

def is_sensitive(permission: Permission) -> bool:
    """
    Indica si una operación requiere controles adicionales.
    """

    return permission in SENSITIVE_PERMISSIONS


def can_apply_payment_plan(
    user_id: str,
    explicit_confirmation: bool,
) -> bool:
    """
    Determina si un usuario puede aplicar un plan de pago.

    La operación requiere:
    1. Usuario autenticado.
    2. Permiso correspondiente.
    3. Confirmación explícita del usuario.
    """

    if not user_id:
        return False

    if not has_permission(
        user_id,
        Permission.APPLY_PAYMENT_PLAN,
    ):
        return False

    return explicit_confirmation