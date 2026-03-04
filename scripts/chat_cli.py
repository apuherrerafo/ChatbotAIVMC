"""
Chat por terminal con Subastin (RAG + historial de conversación).

- Al iniciar envía "hola" para obtener el saludo de bienvenida.
- Mantiene conversation_history y lo pasa en cada llamada a ask_with_router.
- Muestra en terminal: Tú: / Subastin:
- Para salir: escribe "salir" o "exit".

Uso (desde la raíz del proyecto vmc-bot):
  python scripts/chat_cli.py
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")


def main():
    from src.rag.query_rag import ask_with_router

    conversation_history: list[dict] = []

    # Triggerear saludo de bienvenida
    print("Subastin: ", end="", flush=True)
    chunks, answer, _ = ask_with_router("hola", history=conversation_history)
    answer = (answer or "").strip()
    if answer:
        print(answer)
        conversation_history.append({"role": "user", "content": "hola"})
        conversation_history.append({"role": "assistant", "content": answer})
    else:
        print("(No hay respuesta; revisa ANTHROPIC_API_KEY y conexión.)")

    print()

    while True:
        try:
            user_input = input("Tú: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nHasta luego.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("salir", "exit"):
            print("Subastin: Hasta luego. Cuando quieras, aquí estaré. 👋")
            break

        print("Subastin: ", end="", flush=True)
        chunks, answer, _ = ask_with_router(user_input, history=conversation_history)
        answer = (answer or "").strip()
        print(answer)

        conversation_history.append({"role": "user", "content": user_input})
        conversation_history.append({"role": "assistant", "content": answer})
        print()


if __name__ == "__main__":
    main()
