# Resumen para reunión — Qué hemos hecho con el bot VMC

**Para explicar en 2–3 minutos qué está listo y qué hace.**

---

## En una frase

Tenemos un **chatbot que responde preguntas sobre VMC Subastas** usando la información oficial del Centro de Ayuda y las FAQs. Por ahora se prueba en una **página web**; cuando tengamos el número listo, se conecta a WhatsApp.

---

## Qué hace hoy el bot

1. **Recibe una pregunta** (por ejemplo: “¿Qué son los SubasCoins?”, “¿Cuánto cuesta el SubasPass?”, “quiero hablar con alguien”).

2. **Decide qué tipo de consulta es:**
   - Pregunta sobre la plataforma (registro, comisiones, SubasCoins, etc.) → responde con información del Centro de Ayuda.
   - Búsqueda de vehículos (“¿tienen Hilux?”) → por ahora responde que esa función viene pronto y que puede revisar la web.
   - Pedir hablar con un humano → da horarios y datos de contacto (chat, correo).
   - Algo que no tiene que ver con VMC → aclara que solo ayuda con temas de VMC Subastas.

3. **Cuando es una pregunta sobre la plataforma:** busca en una base de conocimiento (texto del Centro de Ayuda y FAQs), elige los fragmentos más relevantes y **Claude (IA)** redacta una respuesta en español peruano, sin inventar números.

4. **SubasPass:** si preguntan por precios o planes de SubasPass, el sistema **consulta la página actual de SubasPass** en ese momento, para que los precios que diga el bot sean los de hoy.

---

## Qué tenemos construido (resumen técnico en lenguaje simple)

| Qué | Para qué sirve |
|-----|-----------------|
| **Base de conocimiento** | Texto del Centro de Ayuda y FAQs ya procesados y organizados por temas. |
| **Búsqueda inteligente** | No busca solo con la pregunta literal; genera variaciones de la pregunta para encontrar mejor la información. |
| **Respuestas con IA** | Claude escribe la respuesta usando solo la información recuperada (no inventa). |
| **Clasificador de intención** | Saber si la persona quiere una respuesta tipo FAQ, buscar autos o hablar con un humano. |
| **Página SubasPass en vivo** | Al preguntar por SubasPass, se lee la página actual para dar precios y planes al día. |
| **Página de prueba** | Una web donde se escribe la pregunta y se ve la respuesta (y de dónde salió la información). Sin WhatsApp todavía. |

---

## Cómo lo probamos hoy

- Entramos a una URL local (por ejemplo `http://127.0.0.1:8001`).
- Escribimos una pregunta en la caja de texto.
- El bot devuelve la respuesta y muestra qué fragmentos de la base de conocimiento usó.

No hay WhatsApp aún porque depende del tema del chip/número; cuando esté, se conecta el mismo flujo.

---

## Qué falta (para que lo expliques si te preguntan)

1. **Contenido en imágenes y videos del Centro de Ayuda**  
   Hoy usamos sobre todo el texto que ya pudimos extraer. Mucha información útil está en infografías y videos; falta un proceso para “leer” esas imágenes y transcribir los videos y meter ese contenido también en la base del bot.

2. **Búsqueda de vehículos con datos reales**  
   Cuando alguien pregunte “¿tienen camionetas?”, el bot debería poder consultar el inventario real; eso implica conectar con los datos de la web de subastas (siguiente fase).

3. **WhatsApp**  
   En cuanto el número esté listo, se configura el enlace con WhatsApp y el mismo bot que probamos en la web responderá por ahí.

4. **Más preguntas de prueba**  
   Tenemos un set pequeño de preguntas con respuestas esperadas para medir si el bot responde bien; la idea es ampliarlo para evaluar mejor.

---

## Frases que puedes usar en la reunión

- “Tenemos un prototipo del bot que ya responde preguntas sobre VMC usando el Centro de Ayuda y las FAQs.”
- “Por ahora se prueba en una página web; cuando tengamos el número, lo conectamos a WhatsApp.”
- “El bot distingue si la persona quiere información, buscar autos o hablar con un humano, y responde en consecuencia.”
- “Para SubasPass consultamos la página actual para dar precios al día.”
- “Lo que falta es incorporar la información que está en imágenes y videos del Centro de Ayuda, y después la búsqueda de vehículos con datos reales.”

Si quieres, puedo acortar esto a media página para que sea aún más fácil de leer en la reunión.
