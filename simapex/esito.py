# -*- coding: utf-8 -*-
"""Valuta da solo se un setup nuovo è andato meglio, uguale o peggio, da tempi e telemetria."""

MIN_GIRI = 4
SOGLIA_MS = 150


def _puliti(g, migliore):
    return [x for x in g if x["tempo_ms"] <= migliore * 1.07]


def _top3(g):
    t = sorted(x["tempo_ms"] for x in g)[:3]
    return sum(t) / len(t)


def _t(v):
    """Momento da cui vale il setup nuovo (per F1: quando il pilota lo ha messo nel gioco)."""
    return v.get("ts_applicato") or v["id"]


def valuta(giri, voce, prossimo_id=None, precedente_id=None):
    """giri: giri registrati; voce: riga del quaderno (id = momento di creazione del setup nuovo).
    Confronta i giri prima (setup precedente) con quelli dopo (setup nuovo). None se i giri non bastano."""
    stessi = [x for x in giri if x["auto"] == voce["auto"] and x["pista"] == voce["pista"] and x.get("ts")]
    prima = [x for x in stessi if x["ts"] < _t(voce) and (precedente_id is None or x["ts"] >= precedente_id)]
    dopo = [x for x in stessi if x["ts"] >= _t(voce) and (prossimo_id is None or x["ts"] < prossimo_id)]
    if not prima or not dopo:
        return None
    migliore = min(x["tempo_ms"] for x in prima + dopo)
    p, d = _puliti(prima, migliore), _puliti(dopo, migliore)
    if len(p) < MIN_GIRI or len(d) < MIN_GIRI:
        return None
    delta = _top3(d) - _top3(p)            # negativo = più veloce
    soglia = max(SOGLIA_MS, 0.0015 * migliore)
    bl_p = sum(len(x.get("blocchi", [])) for x in p) / len(p)
    bl_d = sum(len(x.get("blocchi", [])) for x in d) / len(d)

    def costanza(g):
        t = [x["tempo_ms"] for x in g]
        return max(t) - min(t)
    cp, cd = costanza(p), costanza(d)
    if delta <= -soglia:
        esito = "meglio"
    elif delta >= soglia:
        esito = "peggio"
    elif bl_d - bl_p <= -0.5 or cd < cp * 0.6:
        esito = "meglio"
    elif bl_d - bl_p >= 0.5 or cd > cp * 1.6:
        esito = "peggio"
    else:
        esito = "uguale"
    motivo = "Media dei 3 giri migliori: %s%.2f secondi rispetto a prima (%d giri prima, %d dopo)." % (
        "+" if delta > 0 else "", delta / 1000.0, len(p), len(d))
    if abs(bl_d - bl_p) >= 0.3:
        motivo += " Blocchi in frenata per giro: da %.1f a %.1f." % (bl_p, bl_d)
    motivo += " Con condizioni diverse (carburante, gomme, meteo) il confronto può sbagliare."
    return {"esito": esito, "motivo": motivo}


def aggiorna(quaderno, giri):
    """Compila gli esiti mancanti (non tocca quelli segnati a mano). Ritorna True se qualcosa è cambiato."""
    cambiato = False
    voci = sorted(quaderno, key=lambda x: x.get("id", 0))
    for i, v in enumerate(voci):
        if v.get("esito") and not v.get("esito_auto"):
            continue
        if v.get("f1") and not v.get("ts_applicato"):
            continue
        succ = next((_t(w) for w in voci[i + 1:] if w["auto"] == v["auto"] and w["pista"] == v["pista"] and (not w.get("f1") or w.get("ts_applicato"))), None)
        prec = next((_t(w) for w in reversed(voci[:i]) if w["auto"] == v["auto"] and w["pista"] == v["pista"] and (not w.get("f1") or w.get("ts_applicato"))), None)
        r = valuta(giri, v, succ, prec)
        if r and (v.get("esito") != r["esito"] or v.get("esito_motivo") != r["motivo"]):
            v["esito"], v["esito_motivo"], v["esito_auto"] = r["esito"], r["motivo"], True
            cambiato = True
    return cambiato
