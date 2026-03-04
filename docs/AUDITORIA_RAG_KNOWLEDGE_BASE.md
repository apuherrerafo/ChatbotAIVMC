# Auditoría RAG — VMC-Bot Knowledge Base

**Fecha:** 2026 (según contexto del proyecto)  
**Fuentes:** 515 conversaciones Intercom (320 mensajes categorizados), FAQ oficial (`data/raw/faqs_vmc.md`), RAG actual (`data/processed/chunks.json`, `faq_chunks.json`, `rag_audit_summary.json`), Centro de Ayuda (artículos e infografías).

---

## A) GAPS DE CONOCIMIENTO

Qué preguntan los usuarios que el bot **no** puede responder bien con el conocimiento actual (FAQ + chunks de Centro de Ayuda).

### 1. Pago / Saldo / Billetera (15% — prioridad alta)

| Pregunta real (tipo Intercom) | ¿Cubierto en FAQ/RAG? | Acción sugerida |
|------------------------------|------------------------|------------------|
| "Hice una recarga de 50 dólares en BCP y no figura mi saldo" | FAQ dice "hasta 24 h hábiles"; no dice qué hacer si **no** aparece. | Añadir al RAG: "Si después de 24 h hábiles tu recarga no se refleja, verifica que usaste el CUU correcto y que el comprobante esté cargado. Si sigue sin figurar, contacta a soporte (chat o contigo@vmcsubastas.com)." |
| "Acabo de realizar el pago y lo he enviado por su página, a la espera de confirmación" | No hay texto explícito sobre "confirmación de pago" ni tiempos de validación. | Añadir: plazos de validación de recarga/pago (ej. "hasta 24 h hábiles") y que la confirmación se ve en Billetera → Transacciones. |
| "¿Cuánto es el saldo que debemos pagar por la unidad adjudicada?" | FAQ: pago del activo al vendedor, no con SubasCoins. No hay "cuánto pagar" por unidad. | El monto lo define cada oferta; añadir que debe revisar en Tu Actividad / Resumen de oferta el monto a pagar al vendedor y que el bot no tiene acceso a su cuenta. |

**Tema que aparece en Intercom y no en Centro de Ayuda:** Reclamos por recarga que "no figura", seguimiento de pagos ya enviados, consultas de saldo pendiente por adjudicación.

---

### 2. Subasta En Vivo (11.6%)

| Pregunta real | Cobertura | Acción |
|---------------|-----------|--------|
| "Si uno ingresa a la subasta en vivo y no participa en ofertar, ¿tiene penalidad?" | Sí: responsabilidad de enviar al menos un bid; sanción si no. Está en FAQ y en artículo participantes/sanciones. | Mejorar chunk/FAQ: frase directa "Si consignas y no envías ningún bid en la oferta En Vivo, hay penalidad (retención consignación hasta 23:59:59, -15 puntos, etc.)." |
| "Si uno gana una subasta ¿cuánto tiempo te dan para depositar?" | FAQ: 2 días hábiles posteriores a la habilitación para cumplir responsabilidades (comisión, documentación, pago). No dice "depositar" explícitamente. | Añadir variante: "Tienes 2 días hábiles desde que te habilitan para pagar la comisión, subir documentos y realizar el pago del activo según las condiciones del vendedor." |
| "¿Cómo es la subasta en VMC?" | Hay contenido En Vivo (qué es, precio base, reserva, bids). | Asegurar que el chunk "Lo más consultado" y "Oferta En Vivo" salgan para preguntas muy genéricas; posible parafraseo en golden. |

---

### 3. Proceso de Compra / Adjudicación (10.6%)

| Pregunta real | Cobertura | Acción |
|---------------|-----------|--------|
| "Gané una subasta, el vehículo lo puedo poner a nombre de mi hijo?" | FAQ: "Los activos saldrán únicamente a nombre del titular de la cuenta." | Ya cubierto; reforzar en RAG una frase explícita: "No se puede poner el vehículo a nombre de un tercero (ej. hijo); solo a nombre del titular de la cuenta." |
| "¿Cómo va el proceso de adjudicación de un lote que gané?" | Artículos "Gané una oferta En Vivo", "He sido habilitado para comprar" y FAQ proceso de compra. | El contenido existe pero está repartido; considerar un chunk resumen "Pasos después de ganar: 1) Habilitación (vendedor hasta 10 d hábiles), 2) En 2 d hábiles: comisión, documentación, pago al vendedor." |
| "¿Cuántos días tengo para realizar la compra?" | FAQ: 2 días hábiles posteriores a la habilitación. | Cubierto; asegurar que aparezca en búsqueda por "días" y "compra". |

---

### 4. Registro / Cuenta (9.1%)

| Pregunta real | Cobertura | Acción |
|---------------|-----------|--------|
| "Recuperar los SubasCoins a mi cuenta" | Hay artículo transferencia SubasCoins a SubasWallet; "recuperar" puede ser confusión con transferencia o con recuperar cuenta. | Añadir: si se refiere a recuperar **cuenta** (contraseña), enlace a "recordar contraseña" / soporte; si es **SubasCoins**, aclarar que no se "recuperan" a otra cuenta VMC salvo transferencia a SubasWallet (SubasCars). |
| "Eliminar la información que asigné como empresa" | No hay en FAQ ni en chunks. | Gap claro: el bot debe escalar o decir que para cambios de datos (empresa, RUC, etc.) debe contactar soporte. |
| "¿Cómo me registro?" | Muy cubierto (FAQ + artículo Registro). | OK; mantener en golden. |

---

### 5. Vehículo Específico (3.8%)

| Pregunta real | Cobertura | Acción |
|---------------|-----------|--------|
| "¿Tienen una Hilux 2020?" / "¿Dónde encuentro las bases de cada auto?" / "Quieren ver una unidad con placa X" | No hay catálogo de vehículos ni bases por auto en el RAG. El inventario (scripts/inventario) es otro flujo. | El bot debe responder que el catálogo y disponibilidad se ven en la web (vmcsubastas.com), no que "sí tenemos X modelo"; y para bases/detalle, enlace al detalle de la oferta. Añadir 1 chunk: "Para ver vehículos disponibles y bases de cada oferta, revisa el detalle de cada publicación en la plataforma." |

---

### 6. Visitas (2.8%)

| Pregunta real | Cobertura | Acción |
|---------------|-----------|--------|
| "Quisiera agendar una visita para ver la camioneta en Lurín" / "Coordinar la visita de inspección" | FAQ y artículos: verificar en detalle de oferta si tiene visitas, agendar por plataforma. No hay "Lurín" ni ubicaciones. | Añadir: "Las visitas se agendan desde la plataforma según la oferta; la ubicación (ej. Lurín) depende del vendedor y suele verse en el detalle o al agendar." Escalar si piden lugar/contacto específico. |

---

### 7. Penalidad / Riesgo (0.9%)

| Pregunta real | Cobertura | Acción |
|---------------|-----------|--------|
| "¿Por qué mi marcador figura riesgo alto?" / "¿Por qué riesgo alto y -15?" | Hay artículo riesgo usuario y sanciones; -15 puntos está en sanciones por no enviar bid. | Verificar que chunks de riesgo y sanciones tengan "riesgo alto" y "-15 puntos" bien recuperables; si no, añadir frase explícita al RAG. |

---

## B) CONTENIDO DESACTUALIZADO O INCORRECTO

- **Precios / montos:** El FAQ y los artículos no fijan montos (comisión por oferta, mínimo SubasCoins, etc.); eso está "en el detalle de cada oferta". No se detectó contradicción numérica.
- **Plazos:** 14 días inactividad → baja de cuenta; 2 días hábiles post-habilitación; hasta 24 h hábiles recarga; 10 días hábiles vendedor para habilitar. Coherente entre FAQ y chunks.
- **Nombres de botones / pantallas:** Se mencionan "Participa", "CUU", "Zona de Usuario", "Tu Actividad", "Billetera → Transacciones". Revisar en próxima actualización del Centro de Ayuda que no hayan cambiado (ej. "Mi Actividad" vs "Tu Actividad").
- **Riesgo:** En `rag_audit_summary.json` varios temas (Comisión, Devolución de saldo, Ganador habilitado, Pago y Pacífico, Sanciones) figuran como "missing_topics_in_chunks" pero el contenido **sí existe** en artículos etiquetados como "General" o en artículos específicos (comisión, devolución, habilitado, código Pacífico, sanciones). No es que esté mal, sino que la taxonomía de topics en chunks no tiene siempre un topic dedicado; la recuperación por texto sigue siendo posible.

---

## C) PREGUNTAS FRECUENTES SIN COBERTURA O A MEJORAR

Priorizadas por frecuencia (Intercom):

1. **Recarga en BCP y no figura mi saldo** — Añadir respuesta tipo: plazos 24 h hábiles, revisar CUU y comprobante, y contacto soporte si persiste.
2. **Confirmación de pago / envío de comprobante** — Dónde subir comprobante (Tu Actividad) y que la validación puede tardar.
3. **Cuánto tengo que pagar por la unidad adjudicada** — Revisar en Tu Actividad / oferta; pago al vendedor, no con SubasCoins.
4. **Penalidad si entro a la subasta en vivo y no oferto** — Sí; explicar retención, -15 puntos y devolución en SubasCoins si consignó en dólares.
5. **Tiempo para depositar después de ganar** — 2 días hábiles desde habilitación para cumplir todo el proceso.
6. **¿Cómo es la subasta en VMC?** — Resumen corto: En Vivo (bids en tiempo real), Negociable (propuestas al vendedor); consignación y reglas en el Centro de Ayuda.
7. **Poner el vehículo a nombre de otro (ej. hijo)** — No; solo titular de la cuenta.
8. **Pasos después de ganar / proceso de adjudicación** — Chunk resumen: habilitación → 2 d hábiles → comisión + documentación + pago vendedor.
9. **Recuperar SubasCoins / cuenta** — Diferenciar recuperar cuenta (soporte/recordar contraseña) vs transferencia SubasCoins a SubasWallet.
10. **Eliminar o cambiar datos de empresa (RUC, etc.)** — No cubierto; escalar a soporte.

---

## D) RECOMENDACIONES PARA EL GOLDEN DATASET

20 pares pregunta–respuesta basados en Intercom + FAQ, para evaluación del bot.

```
Q: Hice una recarga en BCP y no me figura el saldo, ¿qué hago?
A: La recarga en dólares puede tardar hasta 24 horas hábiles en reflejarse. Verifica que usaste tu CUU correcto y que cargaste el comprobante si aplica. Si después de ese plazo no ves el saldo, contacta por chat o a contigo@vmcsubastas.com.
CATEGORIA: billetera
DIFICULTAD: media

Q: ¿Cuánto tiempo tengo para pagar después de ganar una subasta?
A: Tienes 2 días hábiles posteriores a la habilitación para cumplir tus responsabilidades: pago de la comisión, carga de documentación y pago del activo al vendedor según las condiciones de la oferta.
CATEGORIA: compra
DIFICULTAD: fácil

Q: Si entro a la subasta en vivo y no envío ningún bid, ¿me penalizan?
A: Sí. Al consignar te comprometes a enviar al menos un bid válido durante el proceso En Vivo. Si no lo haces, la consignación se retiene hasta las 23:59:59 del mismo día, pierdes 15 puntos y si consignaste en dólares te devuelven en SubasCoins.
CATEGORIA: penalidad
DIFICULTAD: media

Q: ¿Puedo poner el vehículo que gané a nombre de mi hijo?
A: No. Los activos salen únicamente a nombre del titular de la cuenta. No se puede comprar a nombre de un tercero.
CATEGORIA: compra
DIFICULTAD: fácil

Q: Acabo de pagar y envié el comprobante por la página, ¿cuándo lo confirman?
A: La validación de pagos y recargas puede tomar hasta 24 horas hábiles. Puedes revisar el estado en tu Zona de Usuario → Billetera → Transacciones. Si pasa ese tiempo y no ves el cambio, contacta a soporte.
CATEGORIA: billetera
DIFICULTAD: media

Q: ¿Cuánto es el saldo que debo pagar por la unidad que me adjudicaron?
A: El monto a pagar por el activo lo define cada oferta y el vendedor. Debes revisar en Tu Actividad el Resumen de oferta y las instrucciones de pago. El pago del activo se hace al vendedor (nunca con SubasCoins).
CATEGORIA: compra
DIFICULTAD: media

Q: ¿Cómo es la subasta en VMC?
A: En VMC hay ofertas En Vivo (subasta en tiempo real con bids) y ofertas Negociables (propuestas directas al vendedor). Para participar debes estar registrado y consignar; en En Vivo debes enviar al menos un bid. Los detalles están en el Centro de Ayuda.
CATEGORIA: subasta
DIFICULTAD: fácil

Q: ¿Cómo me registro?
A: Necesitas DNI, nombre completo, correo y celular. El registro se hace en la web; si quieres factura con RUC, en "Quiero recibir" elige "Factura". El proceso está paso a paso en el Centro de Ayuda (Registrarte es fácil y rápido).
CATEGORIA: registro
DIFICULTAD: fácil

Q: ¿Por qué mi marcador figura riesgo alto?
A: El riesgo usuario depende de tu historial en la plataforma (cumplimiento, sanciones, etc.). Puedes mejorar tu perfil cumpliendo responsabilidades y consultando las condiciones. Los detalles de las categorías de riesgo están en el Centro de Ayuda.
CATEGORIA: penalidad
DIFICULTAD: difícil

Q: Quiero agendar una visita para ver un vehículo en Lurín.
A: Las visitas se agendan desde la plataforma según cada oferta. En el detalle de la oferta verifica si tiene opción a visitas; la ubicación (por ejemplo Lurín) depende del vendedor y suele verse al agendar. Si no hay opción a visitas, el vendedor las inhabilitó o se copó el aforo.
CATEGORIA: visitas
DIFICULTAD: media

Q: ¿Tienen una Hilux 2020?
A: El catálogo de vehículos disponibles lo ves en la plataforma (vmcsubastas.com). Cada oferta tiene su detalle y bases; para ver un modelo o placa específica revisa el listado y el detalle de cada publicación.
CATEGORIA: vehiculo_especifico
DIFICULTAD: fácil

Q: ¿Cómo recupero mis SubasCoins a mi cuenta?
A: Si te refieres a transferir SubasCoins a tu SubasWallet de SubasCars, usa tu SubasName en la opción "Solicitar" (banner); la transferencia puede demorar hasta 2 días hábiles y es irreversible. Si es recuperar acceso a tu cuenta, usa "Recordar contraseña" o contacta a soporte.
CATEGORIA: billetera
DIFICULTAD: media

Q: ¿Cuándo me devuelven la consignación?
A: La consignación retorna a tu billetera al finalizar el proceso de la oferta, salvo que incumplas (por ejemplo no enviar al menos un bid en En Vivo) o resultes ganador habilitado o mejor postor, en cuyo caso se usa según las condiciones.
CATEGORIA: consignación
DIFICULTAD: fácil

Q: ¿Dónde veo el porcentaje de comisión?
A: El porcentaje de comisión de cada oferta lo ves en el detalle de la publicación. La comisión se calcula sobre el bid del ganador habilitado y no está incluida en el bid.
CATEGORIA: comisión
DIFICULTAD: fácil

Q: Fui habilitado para comprar, ¿qué hago?
A: Tienes 2 días hábiles para pagar la comisión (se debita de tu Billetera), subir la documentación que pide el vendedor y seguir las instrucciones de pago del vendedor. Entra a tu Zona de Usuario (clic en tu CUU) → Tu Actividad → Proceso de compra.
CATEGORIA: compra
DIFICULTAD: fácil

Q: ¿Puedo solicitar devolución de mi saldo en dólares?
A: Sí, desde Billetera → Transacciones en tu Zona de Usuario, salvo que tengas consignaciones activas, seas ganador o mejor postor, proceso de compra activo, deuda pendiente, riesgo Alto, o no cumplas el mínimo (ej. US$ 30). Aplica fee y plazos (ej. hasta 7 d hábiles BCP).
CATEGORIA: billetera
DIFICULTAD: media

Q: ¿Cómo pago con el código de pago de Pacífico?
A: En Banca Web o Móvil del BCP: Pago de Servicios → Pacífico Seguros → opción indicada (ej. 23 Deducibles Autos Dólares). Usas la placa del activo como código de pago y luego adjuntas el comprobante en Tu Actividad.
CATEGORIA: compra
DIFICULTAD: media

Q: ¿Puedo eliminar o cambiar la información que puse como empresa (RUC)?
A: Para cambios de datos de empresa o RUC debes contactar a soporte (chat o contigo@vmcsubastas.com), ya que pueden tener restricciones según las políticas de la plataforma.
CATEGORIA: registro
DIFICULTAD: media

Q: ¿Cuánto demora la recarga en dólares?
A: Mediante transferencia o depósito en BCP con tu CUU puede tardar hasta 24 horas hábiles en reflejarse en tu billetera.
CATEGORIA: billetera
DIFICULTAD: fácil

Q: ¿Qué pasa si no cumplo como ganador habilitado?
A: Debes pagar la comisión de todos modos. Pueden aplicarte sanciones: cuenta inhabilitada 7 días calendario, cobro de comisión, pérdida de puntos. Tres incumplimientos con el mismo vendedor pueden llevar a suspensión permanente con ese vendedor.
CATEGORIA: penalidad
DIFICULTAD: fácil
```

---

## E) TEMAS QUE EL BOT DEBE ESCALAR A HUMANO

El bot **no** debe intentar resolver y debe derivar a soporte (chat o contigo@vmcsubastas.com):

1. **Nombres de asesores o personas concretas:** "Quiero hablar con la srta. Saydi", "Betsy Salinas me atendió".
2. **Disputas de pagos ya realizados:** "Ya pagué y no me reconocen", "Me descontaron dos veces".
3. **Problemas con deudas del vehículo (Caja Huancayo, etc.):** "En notaría me dijeron que el vehículo tiene deuda con Caja Huancayo".
4. **Solicitudes que requieren acción interna de VMC:** Cambios masivos de datos, revisión manual de documentos, excepciones de plazos, reclamos formales.
5. **Casos con datos muy específicos (número de operación, placa con seguimiento):** "Sigan mi operación 12345", "¿Por qué mi placa X no pasó inspección?" cuando implique revisión de expediente.
6. **Quejas sobre atención previa o trato:** "Fui mal atendido", "No me han resuelto desde hace semanas".

**Sugerencia de implementación:** En el router o en el system prompt, detectar intención "escalation" cuando haya menciones a: nombre de asesor, "ya pagué y", "caja huancayo", "notaría", "deuda del vehículo", "reclamo", "no me reconocen", "operación número", etc., y responder con un mensaje tipo: "Para este tema necesitas que te atienda directamente el equipo. Escríbenos por chat (Lun–Vie 9am–6pm) o a contigo@vmcsubastas.com."

---

## SCORE DE COBERTURA DEL CONOCIMIENTO ACTUAL

**Score: 6.5 / 10**

- **Fortalezas:** FAQ oficial bien cubierto en `faq_chunks.json` (40 pares); Centro de Ayuda con artículos de comisión, habilitación, consignación, En Vivo, negociable, visitas, riesgo, sanciones; golden actual (50 entradas) alineado con FAQ e infografías.
- **Debilidades:** (1) La categoría más frecuente en Intercom (Pago/Saldo/Billetera 15%) tiene gaps claros: "recarga no figura", "confirmación de pago", "cuánto pagar por unidad". (2) Vehículo específico y eliminación/cambio de datos empresa sin cobertura. (3) Parte del contenido útil está en chunks con mucho ruido (URLs de imágenes, texto de infografías), lo que puede diluir la precisión del RAG. (4) Temas como "Comisión", "Devolución de saldo", "Pago Pacífico" no tienen topic dedicado en chunks (sí en golden), aunque el contenido existe en artículos.

**Para subir el score:** Añadir chunks o FAQ explícitos para: recarga no reflejada, confirmación de pago/comprobante, monto a pagar por adjudicación, penalidad por no ofertar en vivo (frase directa), y regla de escalación para pagos disputados, deudas del vehículo y menciones a asesores. Incluir los 20 pares de la sección D en el golden dataset y ejecutar `eval_golden` para monitorear.
