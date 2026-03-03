# Pinecone — Qué hacer paso a paso

Guía para crear la cuenta, el índice y sacar la API key. Así podrás ejecutar `python -m src.rag.embed` y subir los chunks del Centro de Ayuda.

---

## 1. Crear cuenta

1. Entra en **[app.pinecone.io](https://app.pinecone.io)** (o [pinecone.io](https://www.pinecone.io) y clic en "Sign up").
2. Regístrate con tu correo (o Google/GitHub si lo ofrecen).
3. Elige el plan **Starter** (gratis) si te lo preguntan.

---

## 2. Sacar la API Key

1. Dentro de la consola de Pinecone, en el menú lateral busca **"API Keys"** o **"Keys"** (a veces está en la sección de tu organización o en configuración).
2. Verás una API key ya creada (o un botón **"Create API Key"**).
3. **Cópiala** y guárdala en un lugar seguro (la vas a pegar en el `.env`).
4. En la carpeta del proyecto `vmc-bot`, abre el archivo **`.env`** y añade o completa:
   ```env
   PINECONE_API_KEY=tu_key_que_copiaste
   PINECONE_INDEX_NAME=vmc-bot-rag
   ```
   (Sustituye `tu_key_que_copiaste` por la key real.)

---

## 3. Crear el índice (donde se guardan los textos y sus embeddings)

En Pinecone hay dos formas típulas de crear un índice. Usa la que veas en tu pantalla.

### Opción A — Índice con “embedding” integrado (recomendado)

Si en la consola ves algo como **"Create index"** y te deja elegir un **modelo de embedding** o **"Embedding model"**:

1. Clic en **"Create index"** (o "New index").
2. **Name:** escribe exactamente: **`vmc-bot-rag`**.
3. Donde diga **Embedding model** o **Model**, elige uno en español si existe (por ejemplo **multilingual-e5-large** o **multilingual**). Si no ves ese, elige cualquiera que sea **multilingual** o **default**.
4. Donde pregunte por el **campo de texto** (a veces "Source field" o "Text field" o "Field map"):
   - Si te pide un **nombre de campo**, escribe: **`text`**.
   - Eso es lo que usa nuestro script: cada registro tiene un campo llamado `text` con el fragmento del Centro de Ayuda.
5. **Region / Cloud:** deja la que venga por defecto (por ejemplo AWS y us-east-1).
6. Guarda o crea el índice.

Cuando termine de crearse (puede tardar un minuto), ya puedes usar el script de embed.

### Opción B — Índice “clásico” (solo vectores, sin modelo integrado)

Si **no** ves opción de “embedding model” y solo te piden **dimension**, **metric** y nombre:

1. **Name:** **`vmc-bot-rag`**.
2. **Dimension:** **1024** (es la que usa el modelo multilingual-e5-large).
3. **Metric:** **cosine**.
4. Crea el índice.

En este caso nuestro script **no** funcionará tal cual, porque está pensado para enviar **texto** y que Pinecone convierta a vectores. Con índice clásico tendrías que:
- o bien generar los vectores con otro servicio (por ejemplo otro API de embeddings) y subir vectores en lugar de texto,
- o bien usar la Opción A si tu plan lo permite.

Por eso, si puedes, usa la **Opción A**.

---

## 4. Comprobar que todo está listo

En tu `.env` deberías tener:

```env
PINECONE_API_KEY=pcsk_... (o similar)
PINECONE_INDEX_NAME=vmc-bot-rag
```

Y en la consola de Pinecone:

- Un índice llamado **vmc-bot-rag**.
- Si es con embedding: que el campo de texto sea **`text`** (o el que hayas configurado y que coincida con lo que dice la Opción A).

---

## 5. Subir los chunks del Centro de Ayuda

En la terminal, desde la carpeta del proyecto:

```bash
cd c:\ChatBotAI\vmc-bot
python -m src.rag.embed
```

Si algo falla, el script suele decir si es por API key, nombre del índice o formato del índice. Con la Opción A y el campo `text` debería funcionar.

---

## Resumen rápido

| Paso | Dónde | Qué hacer |
|------|--------|-----------|
| 1 | app.pinecone.io | Crear cuenta (Starter gratis). |
| 2 | Consola → API Keys | Copiar API key y ponerla en `vmc-bot/.env` como `PINECONE_API_KEY=...`. |
| 3 | Consola → Create index | Nombre: `vmc-bot-rag`. Elegir embedding model y campo de texto **`text`** (Opción A). |
| 4 | `.env` | Ver que estén `PINECONE_API_KEY` y `PINECONE_INDEX_NAME=vmc-bot-rag`. |
| 5 | Terminal | `python -m src.rag.embed` para subir los chunks. |

Si en algún paso la consola no se parece a esto (por ejemplo no ves "Embedding model"), dime qué opciones te salen y adaptamos los pasos.
