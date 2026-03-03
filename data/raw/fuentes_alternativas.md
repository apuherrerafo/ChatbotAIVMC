# Fuentes alternativas para la base de conocimiento

Exploración para complementar el Centro de Ayuda (ayuda.vmcsubastas.com).  
Revisar manualmente cuando sea posible; el sitio principal puede tardar en responder.

---

## URLs a revisar

| Fuente | URL sugerida | Prioridad | Notas |
|--------|--------------|-----------|--------|
| Sitio principal | https://www.vmcsubastas.com | Alta | Footer suele tener T&C, Ayuda, Contacto |
| Términos y Condiciones | https://www.vmcsubastas.com/condiciones-y-terminos | Crítica | Números y plazos oficiales |
| Política de privacidad | https://www.vmcsubastas.com/privacidad (o /privacy) | Media | |
| FAQ / Ayuda | https://www.vmcsubastas.com/ayuda o enlace al Centro de Ayuda | Alta | Ya tenemos ayuda.vmcsubastas.com |
| robots.txt | https://www.vmcsubastas.com/robots.txt | Baja | Ver si hay sitemap URL |
| Sitemap | https://www.vmcsubastas.com/sitemap.xml | Baja | Lista de URLs del sitio |
| Inventario / subastas | Según Roadmap: scraping 2x/día en Semana 3 | Fase 2 | No es texto estático; será JSON/datos |

---

## Cómo completar esta lista

1. Abrir en el navegador las URLs de la tabla y anotar las que existan.
2. Si hay T&C o FAQ en texto, guardar el contenido en `data/raw/legal/` o `data/raw/faq/`.
3. Actualizar esta tabla con las URLs reales y si tienen texto útil.

---

## FAQs oficiales VMC

- **Archivo:** `data/raw/faqs_vmc.md` (texto) y `data/processed/faq_chunks.json` (chunks para RAG).
- **Golden dataset:** `data/golden_dataset/faqs_golden.json` (preguntas con respuesta esperada para evaluación).
- **Pinecone:** Los 40 FAQs están subidos al namespace `helpcenter` (ejecutar `python -m src.rag.embed_faqs` si se actualiza el JSON).

## Centro de Ayuda ya crawleado

- **Archivo:** `data/raw/helpcenter_crawl.json`
- **Páginas:** 25 (registro, oferta En Vivo, SubasCoins, billetera, consignación, visitas, SubasTour, etc.)
- **Markdown completo:** Ejecutar `python -m src.ingest.export_helpcenter_markdown` para guardar cada artículo en `data/raw/text/`.
