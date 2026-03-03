"""
Reciprocal Rank Fusion (RRF): fusiona resultados de varias búsquedas en una sola lista.
Cada resultado es un dict con al menos "id". Se usa score RRF = sum(1 / (k + rank)).
Sin LangChain; función pura en Python.
"""
# k constante típica (evita división por cero y suaviza)
RRF_K = 60


def reciprocal_rank_fusion(list_of_results, k=RRF_K, id_key="id"):
    """
    list_of_results: lista de listas; cada lista son los hits de una búsqueda (ordenados por relevancia).
    Cada hit es un dict con al menos id_key (por defecto "id"); el resto se conserva del mejor ranking.
    Devuelve una sola lista ordenada por score RRF descendente, sin duplicados por id.
    """
    if not list_of_results:
        return []
    # score por id: sum(1 / (k + rank))
    scores = {}
    # guardar el objeto completo del primer ranking donde aparece cada id (para conservar text, topic, etc.)
    first_seen = {}
    for rank_list in list_of_results:
        for rank, hit in enumerate(rank_list, start=1):
            hid = hit.get(id_key) or hit.get("_id")
            if hid is None:
                continue
            rrf_inc = 1.0 / (k + rank)
            scores[hid] = scores.get(hid, 0.0) + rrf_inc
            if hid not in first_seen:
                first_seen[hid] = dict(hit)
    # ordenar por score descendente
    sorted_ids = sorted(scores.keys(), key=lambda x: -scores[x])
    out = []
    for hid in sorted_ids:
        item = first_seen[hid].copy()
        item["rrf_score"] = round(scores[hid], 6)
        out.append(item)
    return out
