# -*- coding: utf-8 -*-
"""Riassunto per la pagina telefono: piste, giri migliori, progressi, tempo da raggiungere, prossimo passo.
Viene mandato al deposito dati ogni 2-3 minuti mentre Simapex è aperto (solo lettura dal telefono)."""
import json
import time

from . import community, obiettivi
from .telemetria import formatta_tempo

FILE_DATI = "pc/telefono.json"


def costruisci(cartella, giri, versione, adesso=None):
    adesso = adesso or time.time()
    per = {}
    for g in giri or []:
        if g.get("tempo_ms") and g.get("auto") and g.get("pista"):
            per.setdefault((g["auto"], g["pista"]), []).append(g)
    piste = []
    for (auto, pista), lst in per.items():
        lst = sorted(lst, key=lambda x: x.get("ts") or 0)
        mig = min(x["tempo_ms"] for x in lst)
        ultimi = [x["tempo_ms"] for x in lst[-10:]]
        giorni = {}
        for x in lst:
            gg = time.strftime("%Y-%m-%d", time.localtime(x.get("ts") or 0))
            giorni[gg] = min(giorni.get(gg, 10 ** 9), x["tempo_ms"])
        progressi = [{"giorno": k, "migliore_ms": giorni[k]} for k in sorted(giorni)][-8:]
        voce = {"auto": auto, "pista": pista, "giri": len(lst), "migliore_ms": mig, "migliore": formatta_tempo(mig),
                "ultimo": formatta_tempo(lst[-1]["tempo_ms"]), "ultimi_ms": ultimi, "progressi": progressi,
                "ultimo_ts": lst[-1].get("ts") or 0}
        c = community.stato(cartella, auto, pista, mig)
        if c:
            voce["community"] = {k: c.get(k) for k in ("primo_ms", "mediana_ms", "ultimo_ms", "pct_primo", "pct_mediana", "testo")}
        ob = obiettivi.carica(cartella).get("%s|%s" % (auto, pista)) or {}
        o = ob.get("obiettivo")
        if o:
            voce["obiettivo"] = {"fase": o.get("fase"), "titolo": o.get("titolo"), "testo": o.get("testo"), "esito": ob.get("esito", "")}
        piste.append(voce)
    piste.sort(key=lambda x: -x["ultimo_ts"])
    prossimo = ""
    if piste and piste[0].get("obiettivo"):
        prossimo = piste[0]["obiettivo"]["testo"]
    elif piste:
        prossimo = "Fai 5 giri puliti di fila."
    return {"aggiornato": int(adesso), "versione": versione, "piste": piste, "prossimo_passo": prossimo,
            "calendario": carica_calendario(cartella)}


def carica_calendario(cartella):
    import os
    try:
        with open(os.path.join(cartella, "calendario.json"), "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, list) else []
    except Exception:
        return []


def testo(cartella, giri, versione):
    return json.dumps(costruisci(cartella, giri, versione), ensure_ascii=False)
