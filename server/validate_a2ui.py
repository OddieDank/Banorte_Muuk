"""verify_a2ui: chequeo contra el catálogo. DEBE pasar antes de cada push.

Uso:
  python validate_a2ui.py <archivo.json>  # valida un response del agente
  python validate_a2ui.py                 # self-check con fixtures
"""

import json
import sys

from catalog import CATALOG, validar_componente


def validar_response(componentes: list) -> tuple[bool, list[dict]]:
    falsos = []
    for c in componentes:
        t = c.get("type")
        if not validar_componente(t, c.get("props", {})):
            falsos.append({"type": t, "props": c.get("props")})
    return len(falsos) == 0, falsos


FIXTURES = [
    # (reponse, esperado_ok)
    ([{"type": "PlanDePago",
      "props": {"mensaje": "Opciones",
                "opciones": [{"meses": 12, "pago_mensual": 1, "cat": 30}],
                "cta": "Aplicar"}}], True),
    ([{"type": "PlanDePago",
      "props": {"mensaje": "malo", "opciones": []}}], True),  # vacío pero válido
    ([{"type": "ComponenteFalso", "props": {}}], False),
    ([{"type": "PlanDePago",
      "props": {"mensaje": "X", "opciones": [{"meses": -1, "pago_mensual": 1, "cat": 30}]}}], False),
    ([{"type": "TablaGastos",
      "props": {"titulo": "Gastos", "filas": [{"concepto": "x", "monto": 1, "categoria": "c"}]}}], True),
]


def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            data = json.load(f)
        componentes = data.get("componentes", data if isinstance(data, list) else [])
        ok, errores = validar_response(componentes)
        print("OK" if ok else f"FALLO: {errores}")
        return 0 if ok else 1

    fallos = 0
    for i, (componentes, esperado) in enumerate(FIXTURES):
        ok, _ = validar_response(componentes)
        if ok != esperado:
            print(f"[FAIL] fixture {i}: esperado={esperado} ok={ok}")
            fallos += 1
    print(f"{len(FIXTURES) - fallos}/{len(FIXTURES)} fixtures pasan; catálogo: {list(CATALOG)}")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
