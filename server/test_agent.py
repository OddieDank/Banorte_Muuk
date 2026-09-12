from agent import run_muuk


prompt = """
user_id=a1111111-0000-0000-0000-000000000001
sesion_id=test-session

El usuario pregunta:

¿En qué estoy gastando demasiado?
"""

response = run_muuk(prompt)

print("\n========== RESPUESTA ==========\n")
print(response.model_dump_json(indent=2))