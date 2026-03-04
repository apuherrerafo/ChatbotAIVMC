"""Verifica get_top_k con las 6 preguntas de prueba."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.rag.query_rag import get_top_k

tests = [
    ("Fui habilitado para comprar, que hago primero?", 5),
    ("Que son los SubasCoins?", 3),
    ("Que pasa si no cumplo con mi compra?", 5),
    ("Donde esta mi Zona de Usuario?", 3),
    ("Cuando me devuelven la consignacion?", 5),
    ("Puedo pedir devolucion de mi saldo?", 5),
]
print("query -> top_k (esperado) | OK/FAIL")
for q, exp in tests:
    got = get_top_k(q)
    ok = "OK" if got == exp else "FAIL"
    print(f"  {got} ({exp}) {ok}  | {q[:50]}")
