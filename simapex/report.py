# -*- coding: utf-8 -*-
"""Report di fine sessione: cosa serve sapere a un pilota dopo aver guidato."""
from . import pressioni
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


NOMI_RUOTE = ["ant_sx", "ant_dx", "post_sx", "post_dx"]


def gomme_da_giri(s):
    """Medie gomme della sessione, ricavate dai giri salvati (nello stesso formato del riepilogo live)."""
    g = [x["gomme"] for x in s if x.get("gomme")]
    if not g:
        return None
    n = len(g)
    out = {"giri_con_dati": n,
           "pressione_media_psi": {NOMI_RUOTE[i]: round(sum(x["p"][i] for x in g) / n, 1) for i in range(4)},
           "temperatura_media_C": {NOMI_RUOTE[i]: round(sum(x["t"][i] for x in g) / n) for i in range(4)}}
    gz = [x["z"] for x in g if x.get("z")]
    if gz:
        out["temperatura_zone_C"] = {NOMI_RUOTE[i]: {k: round(sum(z[j][i] for z in gz) / len(gz))
                                                     for j, k in enumerate(("interna", "centro", "esterna"))}
                                     for i in range(4)}
    return out


TIPI = {0: "prove libere", 1: "qualifica", 2: "gara", 3: "giro lanciato", 4: "giro lanciato", 7: "prove libere", 8: "qualifica"}


def tipo_sessione(s):
    """Tipo di sessione dai giri (campo 'sess' letto da ACC); '' se non noto (giri vecchi)."""
    for x in s:
        if x.get("sess") in TIPI:
            return TIPI[x["sess"]]
    return ""


def tutte_le_sessioni(giri):
    """Divide tutti i giri registrati in sessioni (cambia auto/pista o pausa lunga). Dalla più recente."""
    sess, cur = [], []
    for x in giri:
        if cur and (x["auto"] != cur[-1]["auto"] or x["pista"] != cur[-1]["pista"] or
                    (x.get("sess") is not None and cur[-1].get("sess") is not None and x["sess"] != cur[-1]["sess"]) or
                    (x.get("ts") and cur[-1].get("ts") and x["ts"] - cur[-1]["ts"] > PAUSA_SESSIONE_S)):
            sess.append(cur)
            cur = []
        cur.append(x)
    if cur:
        sess.append(cur)
    return list(reversed(sess))


def elenco_sessioni(giri):
    out = []
    for s in tutte_le_sessioni(giri):
        tempi = [x["tempo_ms"] for x in s]
        out.append({"id": s[0].get("ts") or 0, "auto": s[0]["auto"], "pista": s[0]["pista"], "data": s[0].get("ts"),
                    "giri": len(s), "tipo": tipo_sessione(s), "miglior_giro": formatta_tempo(min(tempi)),
                    "blocchi": sum(len(x.get("blocchi", [])) for x in s)})
    return out


def dettaglio_sessione(giri, id_sessione, stile=None):
    for s in tutte_le_sessioni(giri):
        if (s[0].get("ts") or 0) == id_sessione:
            r = crea_report(giri, None, stile, sessione=s)
            carb = [x["carburante"] for x in s if x.get("carburante") is not None]
            r["carburante_inizio"], r["carburante_fine"] = (carb[0], carb[-1]) if carb else (None, None)
            r["data"] = s[0].get("ts")
            return r
    return None


def crea_report(giri, gomme=None, stile=None, sessione=None):
    s = sessione if sessione is not None else ultima_sessione(giri)
    if gomme is None:
        gomme = gomme_da_giri(s)
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
    r = {"auto": s[0]["auto"], "pista": s[0]["pista"], "giri": len(s), "tipo": tipo_sessione(s),
         "miglior_giro": formatta_tempo(migliore),
         "media_migliori_3": formatta_tempo(sum(top) / len(top)) if top else "",
         "costanza_ms": max(x["tempo_ms"] for x in puliti) - min(x["tempo_ms"] for x in puliti) if puliti else 0,
         "giri_lenti_o_sporchi": lenti,
         "dettaglio_giri": [{"giro": x.get("giro"), "tempo": formatta_tempo(x["tempo_ms"]),
                   "blocchi": len(x.get("blocchi", [])), "carburante": x.get("carburante"),
                   "pulito": x["tempo_ms"] <= migliore * 1.07} for x in s],
         "blocchi_totali": len(blocchi), "blocchi_per_ruota": per_ruota,
         "giri_con_blocchi": sorted({g for g, _ in blocchi if g}),
         "gomme": gomme, "stile": stile}
    r["gara"] = _dati_gara(s, puliti) if r["tipo"] == "gara" else None
    r["qualifica"] = _dati_qualifica(s, migliore) if r["tipo"] in ("qualifica", "giro lanciato") else None
    caldo = pressioni.a_caldo(s)
    r["pressioni_caldo"] = {"psi": caldo, "stati": [pressioni.stato(x) for x in caldo]} if caldo else None
    r["note"] = _note(r)
    return r


def _dati_gara(s, puliti):
    pos = [x.get("pos") for x in s if x.get("pos")]
    medi = [x["tempo_ms"] for x in puliti]
    out = {"posizione_inizio": pos[0] if pos else None, "posizione_fine": pos[-1] if pos else None,
           "passo_medio": formatta_tempo(sum(medi) / len(medi)) if medi else "", "calo_passo_ms": None, "consumo_giro": None}
    if len(medi) >= 6:
        t = len(medi) // 3
        out["calo_passo_ms"] = round(sum(medi[-t:]) / t - sum(medi[:t]) / t)
    carb = [x["carburante"] for x in s if x.get("carburante") is not None]
    cons = [a - b for a, b in zip(carb, carb[1:]) if 0 < a - b < 15]
    if cons:
        out["consumo_giro"] = round(sum(cons) / len(cons), 1)
    return out


def _dati_qualifica(s, migliore):
    tempi = sorted(x["tempo_ms"] for x in s)
    return {"secondo_migliore_ms": tempi[1] - tempi[0] if len(tempi) > 1 else None, "giri": len(s)}


def _note(r):
    n = []
    tipo = r.get("tipo")
    if tipo == "gara" and r.get("gara"):
        g = r["gara"]
        if g["posizione_inizio"] and g["posizione_fine"]:
            n.append("Gara: dalla posizione %d alla %d, %d giri, giro più veloce %s." % (g["posizione_inizio"], g["posizione_fine"], r["giri"], r["miglior_giro"]))
        else:
            n.append("Gara: %d giri, giro più veloce %s." % (r["giri"], r["miglior_giro"]))
        if g["passo_medio"]:
            n.append("Passo medio sui giri puliti: %s." % g["passo_medio"])
        if g["calo_passo_ms"] is not None:
            c = g["calo_passo_ms"] / 1000.0
            n.append("Negli ultimi giri sei %s di %.1f s a giro rispetto ai primi%s." % ("più lento" if c > 0 else "più veloce", abs(c), (": le gomme o il carburante stanno calando, gestisci di più" if c > 0.8 else "")))
        if g["consumo_giro"]:
            n.append("Consumo medio: %.1f litri a giro." % g["consumo_giro"])
    elif tipo in ("qualifica", "giro lanciato"):
        q = r.get("qualifica") or {}
        n.append("%s: il tuo giro migliore è %s su %d giri." % (tipo.capitalize(), r["miglior_giro"], r["giri"]))
        if q.get("secondo_migliore_ms") is not None:
            n.append("Il secondo giro migliore è a %.1f s dal primo: %s." % (q["secondo_migliore_ms"] / 1000.0, "sai ripeterti" if q["secondo_migliore_ms"] < 500 else "il giro buono è stato un po' isolato"))
    else:
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
        if r.get("pressioni_caldo"):
            n.append(pressioni.testo_pressioni(r["pressioni_caldo"]["psi"]))
        elif p:
            n.append("Pressione media: " + ", ".join("%s %s psi" % (NOMI.get(k, k), v) for k, v in p.items()) + ".")
        z = g.get("temperatura_zone_C")
        if z:
            for k, v in z.items():
                if v["interna"] - v["esterna"] > 8:
                    n.append("Gomma %s: l'interno è molto più caldo dell'esterno (troppa campanatura negativa?)." % NOMI.get(k, k))
                elif v["esterna"] - v["interna"] > 8:
                    n.append("Gomma %s: l'esterno è più caldo dell'interno (poca campanatura?)." % NOMI.get(k, k))
    return n
