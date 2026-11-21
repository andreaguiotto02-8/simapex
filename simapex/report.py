# -*- coding: utf-8 -*-
"""Report di fine sessione: cosa serve sapere a un pilota dopo aver guidato."""
from .telemetria import formatta_tempo

PAUSA_SESSIONE_S = 20 * 60
NOMI = {"ant_sx": "anteriore sinistra", "ant_dx": "anteriore destra",
        "post_sx": "posteriore sinistra", "post_dx": "posteriore destra"}


def ultima_sessione(giri, auto=None, pista=None):
    """Giri dell'ultima sessione (stessa auto/pista, senza pause lunghe tra un giro e l'altro)."""
    if not giri:
        return []
    if auto is None:
        auto, pista = giri[-1]["auto"], giri[-1]["pista"]
    g = [x for x in giri if x["auto"] == auto and (pista is None or x["pista"] == pista)]
    out = []
    for x in reversed(g):
        if out and out[-1].get("ts") and x.get("ts") and out[-1]["ts"] - x["ts"] > PAUSA_SESSIONE_S:
            break
        out.append(x)
    return list(reversed(out))


def crea_report(giri, gomme=None, stile=None):
    s = ultima_sessione(giri)
    if not s:
        return None
    tempi = [x["tempo_ms"] for x in s]
    migliore = min(tempi)
    puliti = [x for x in s if x["tempo_ms"] <= migliore * 1.07]
    lenti = [x["giro"] for x in s if x["tempo_ms"] > migliore * 1.07]
    top = sorted(x["tempo_ms"] for x in puliti)[:3]
    blocchi = [(x.get("giro"), b) for x in s for b in x.get("blocchi", [])]
    per_ruota = {}
    for _, b in blocchi:
        per_ruota[b["ruota"]] = per_ruota.get(b["ruota"], 0) + 1
    r = {"auto": s[0]["auto"], "pista": s[0]["pista"], "giri": len(s),
         "miglior_giro": formatta_tempo(migliore),
         "media_migliori_3": formatta_tempo(sum(top) / len(top)) if top else "",
         "costanza_ms": max(x["tempo_ms"] for x in puliti) - min(x["tempo_ms"] for x in puliti) if puliti else 0,
         "giri_lenti_o_sporchi": lenti,
         "dettaglio_giri": [{"giro": x.get("giro"), "tempo": formatta_tempo(x["tempo_ms"]),
                   "blocchi": len(x.get("blocchi", []))} for x in s],
         "blocchi_totali": len(blocchi), "blocchi_per_ruota": per_ruota,
         "giri_con_blocchi": sorted({g for g, _ in blocchi if g}),
         "gomme": gomme, "stile": stile}
    r["note"] = _note(r)
    return r


def _note(r):
    n = []
    n.append("Hai fatto %d giri; il migliore è %s." % (r["giri"], r["miglior_giro"]))
    if r["costanza_ms"]:
        c = r["costanza_ms"] / 1000.0
        n.append("Tra i giri puliti c'è %.1f secondi di differenza: %s." % (c, "sei molto costante" if c < 1 else "c'è margine per essere più costante"))
    if r["giri_lenti_o_sporchi"]:
        n.append("Giri lenti o sporchi (non contati): %s." % ", ".join(str(x) for x in r["giri_lenti_o_sporchi"]))
    if r["blocchi_totali"]:
        w = max(r["blocchi_per_ruota"], key=r["blocchi_per_ruota"].get)
        n.append("Hai bloccato %d volte in frenata, soprattutto la ruota %s (giri %s). Prova a frenare un po' meno forte all'inizio e a rilasciare con progressione." % (
            r["blocchi_totali"], NOMI.get(w, w), ", ".join(str(x) for x in r["giri_con_blocchi"])))
    else:
        n.append("Non ho rilevato blocchi in frenata.")
    g = r.get("gomme")
    if g:
        t, p = g.get("temperatura_media_C", {}), g.get("pressione_media_psi", {})
        if t:
            n.append("Temperatura media gomme: " + ", ".join("%s %s°C" % (NOMI.get(k, k), v) for k, v in t.items()) + ".")
        if p:
            n.append("Pressione media: " + ", ".join("%s %s psi" % (NOMI.get(k, k), v) for k, v in p.items()) + ".")
        z = g.get("temperatura_zone_C")
        if z:
            for k, v in z.items():
                if v["interna"] - v["esterna"] > 8:
                    n.append("Gomma %s: l'interno è molto più caldo dell'esterno (troppa campanatura negativa?)." % NOMI.get(k, k))
                elif v["esterna"] - v["interna"] > 8:
                    n.append("Gomma %s: l'esterno è più caldo dell'interno (poca campanatura?)." % NOMI.get(k, k))
    return n
