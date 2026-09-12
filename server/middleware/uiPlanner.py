"""Planificador de UI de Muuk: orden de componentes por preferencia del usuario.

La validación de tipos/props vive en catalog.py (fail-closed).
"""


def prioritize_components(
    components: list[str],
    preferred_components: list[str] | None = None,
) -> list[str]:
    """Ordena componentes: primero los preferidos por el usuario, resto igual."""
    if not preferred_components:
        return components
    preferred = {c: i for i, c in enumerate(preferred_components)}
    return sorted(components, key=lambda c: preferred.get(c, len(preferred)))
