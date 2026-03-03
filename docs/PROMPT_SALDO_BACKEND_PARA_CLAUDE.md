# Prompt para Claude: Saldo Anthropic persistente (backend para Vercel)

Copia y pega este bloque en Claude para darle contexto y que te proponga cómo implementar el saldo con memoria en el backend.

---

## Contexto del proyecto

**VMC-Bot** es un chatbot RAG para VMC Subastas (Perú). Stack relevante:

- **Backend:** FastAPI (Python), Uvicorn. Servidor en `src/server/app.py`.
- **Frontend de prueba:** Una sola página estática `static/index.html` con un formulario de chat y un panel de debug (router, multi-query, retrieval, generación, costo por mensaje).
- **LLM:** Anthropic (Claude Haiku para router + multi-query, Claude Sonnet para la respuesta). Cada mensaje genera un costo estimado en USD que ya se calcula en el backend (`src/server/cost_estimate.py`, `_build_debug_cost` en `app.py`) y se devuelve en `debug.cost.this_message`.
- **Deploy objetivo:** La app se quiere desplegar en **Vercel** para compartirla con alguien. En Vercel el backend corre en **serverless functions** (sin disco persistente por defecto).

## Comportamiento actual del “saldo” (problema)

En el frontend (`static/index.html`) hay un contador que muestra **“Saldo: $X.XX”**:

- Se usa un **saldo inicial fijo** en JS: `STARTING_BALANCE_USD = 5` (los 5 USD que el dueño cargó en Anthropic).
- Por cada respuesta del bot, el frontend suma `debug.cost.this_message` a un acumulador `sessionCostUsd` y muestra **Saldo = 5 - sessionCostUsd**.
- Ese valor solo existe **en memoria en el navegador**: si otra persona abre la app (o la misma en otra pestaña/dispositivo), verá de nuevo Saldo: $5.00. No hay “memoria” compartida ni persistencia. Al recargar la página, el saldo vuelve a 5.

## Objetivo

Que el **saldo tenga memoria en el backend**:

1. **Un solo saldo compartido:** Cualquier usuario que abra la app (por ejemplo en la URL de Vercel) ve el **mismo** saldo (ej. los 5 USD iniciales) y ese saldo **baja** con cada uso de la API, para todos.
2. **Persistencia:** Aunque se reinicie el servidor o se despliegue de nuevo en Vercel, el saldo debe recuperarse (no volver siempre a 5).
3. **Actualización manual cuando se agregue billing:** Cuando el dueño agregue más crédito en la consola de Anthropic, debe poder indicar “agregué X dólares” y que el saldo guardado se actualice (sumar X al saldo actual o fijar un nuevo tope).

En resumen: el frontend debe dejar de calcular el saldo con un 5 fijo en JS y debe **recibir del backend** el saldo actual (y opcionalmente el costo del mensaje que acaba de hacer), de forma que todo el mundo vea cómo bajan esos 5 dólares (o el monto que se haya configurado) conforme se usa la API.

## Restricciones técnicas

- **Vercel:** Las funciones son stateless; no hay sistema de archivos persistente. No se puede guardar el saldo en un `.json` en disco del servidor y esperar que siga ahí en la siguiente invocación.
- **Solución necesaria:** Algún **almacén externo** o servicio que Vercel pueda usar:
  - Ejemplos: **Vercel KV** (Redis), **Vercel Postgres**, **Vercel Blob**, o un servicio externo (Supabase, Upstash Redis, etc.). O, si el deploy no fuera solo Vercel, un backend con disco o DB.
- El backend ya tiene:
  - `POST /api/ask`: recibe `question`, opcionalmente `include_debug` y `session_id`; devuelve `answer`, `chunks`, `intent` y, si hay debug, `debug` con `debug.cost.this_message` (costo del mensaje en USD).
  - No existe hoy ningún endpoint de “saldo” ni ningún almacén de saldo.

## Lo que necesito que me propongas (o implementes)

1. **Dónde guardar el saldo:** Dada la intención de desplegar en Vercel, ¿qué opción recomiendas? (Vercel KV, Vercel Postgres, Blob, Upstash, Supabase, etc.) y por qué. Si hay una opción mínima (por ejemplo un solo key en KV: `anthropic_balance_usd`) descríbela.
2. **API de backend:**
   - **Obtener saldo:** Un endpoint (por ejemplo `GET /api/balance`) que devuelva el saldo actual en USD, para que el frontend lo muestre al cargar y cuando quieras refrescarlo.
   - **Actualizar saldo después de cada mensaje:** En `POST /api/ask`, después de calcular `debug.cost.this_message`, restar ese valor del saldo guardado y devolver en la respuesta (por ejemplo en `balance_remaining_usd` o dentro de `debug`) el nuevo saldo, para que el frontend actualice “Saldo: $X.XX” sin tener que llamar a otro endpoint.
   - **Fijar/recargar saldo (cuando agregue billing):** Un endpoint (por ejemplo `POST /api/balance` o `PUT /api/balance`) que permita **establecer** el saldo actual (o sumar X dólares). Debe estar protegido (por ejemplo con un token o API key en header o query) para que solo el dueño pueda “recargar”. Indicar cómo protegerlo de forma simple.
3. **Inicialización:** La primera vez que se use el almacén, el saldo debería ser 5 (o un valor configurable por env, ej. `ANTHROPIC_INITIAL_BALANCE_USD=5`).
4. **Frontend:** Cambios mínimos en `static/index.html` para que:
   - Al cargar la página llame a `GET /api/balance` (o reciba el saldo en la primera respuesta de algún otro endpoint) y muestre “Saldo: $X.XX”.
   - Tras cada mensaje use el `balance_remaining_usd` (o el campo que definas) que venga en la respuesta de `POST /api/ask` y actualice el contador, en lugar de calcular 5 - sessionCostUsd en JS.
5. **Comportamiento cuando el saldo llegue a 0:** Decidir si el backend debe rechazar nuevas preguntas (por ejemplo 402 o 503 con un mensaje tipo “Saldo agotado”) o solo informar saldo 0 y dejar que el usuario intente igual (y falle por Anthropic si no hay crédito). Recomendación breve.

## Archivos relevantes en el repo

- `src/server/app.py` — FastAPI, `POST /api/ask`, `_build_debug_cost`, historial por `session_id`.
- `static/index.html` — Contador “Saldo: $X.XX”, `sessionCostUsd`, `STARTING_BALANCE_USD = 5`, `updateBalanceDisplay()`.
- `src/server/cost_estimate.py` — Cálculo de costo por mensaje (Haiku router, Haiku multi-query, Sonnet).
- `docs/` — Aquí está este prompt; puede haber otros docs de arquitectura.

No hace falta que cambies la lógica de cálculo de costos ni el flujo RAG; solo añadir persistencia del saldo, endpoints de lectura/escritura de ese saldo, y que el frontend consuma el saldo desde el backend en lugar de calcularlo en memoria con un 5 fijo.

Por favor propón una solución concreta (servicio de almacenamiento, esquema de endpoints, nombres de campos en JSON y, si puedes, los cambios clave en código o pseudocódigo) para que pueda implementarla o seguir tu guía paso a paso.
