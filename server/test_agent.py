from agent import run_muuk


prompt = """
user_id=a3333333-0000-0000-0000-000000000001
sesion_id=test-session

El usuario pregunta:

Quiero pagar mi deuda a 12 meses
"""

response = run_muuk(prompt)

print("\n========== RESPUESTA ==========\n")
print(response.model_dump_json(indent=2))