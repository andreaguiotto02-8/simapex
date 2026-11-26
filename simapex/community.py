# -*- coding: utf-8 -*-
"""Tempi della community: «tempo da raggiungere» per pista/auto (primo, mediana, ultimo) e la percentuale di Otto."""
import json
import os
import re
import urllib.request

from .telemetria import formatta_tempo

_TEMPO = re.compile(r"\b([1-9]):([0-5]\d)[.,](\d{3})\b")


def _file(cartella):
    return os.path.join(cartella, "community_tempi.json")


def carica(cartella):
    try:
        with open(_file(cartella), "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _chiave(auto, pista):
    return "%s|%s" % (auto, pista)


def estrai_tempi(testo):
    """Tutti i tempi sul giro (m:ss.mmm) trovati in un testo/pagina, in ms. Scarta i valori troppo lontani dal migliore (altri campi)."""
    t = [int(m) * 60000 + int(s) * 1000 + int(ms) for m, s, ms in _TEMPO.findall(testo or "")]
    if not t:
        return []
    b = min(t)
    return sorted(x for x in t if x <= b * 1.5)


def riassunto(tempi):
    """(primo, mediana, ultimo) in ms oppure None."""
    t = sorted(tempi or [])
    if len(t) < 3:
        return None
    return {"primo_ms": t[0], "mediana_ms": t[len(t) // 2], "ultimo_ms": t[-1], "n": len(t)}


def salva(cartella, auto, pista, primo_ms, mediana_ms, ultimo_ms, fonte="manuale"):
    d = carica(cartella)
    d[_chiave(auto, pista)] = {"auto": auto, "pista": pista, "primo_ms": int(primo_ms), "mediana_ms": int(mediana_ms),
                               "ultimo_ms": int(ultimo_ms), "fonte": fonte}
    os.makedirs(cartella, exist_ok=True)
    with open(_file(cartella), "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    return d[_chiave(auto, pista)]


def leggi_da_url(url, timeout=15):
    """Legge una pagina risultati (SimGrid o altra) e ne estrae i tempi. Ritorna riassunto o None."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 Simapex"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        testo = r.read(3000000).decode("utf-8", "replace")
    return riassunto(estrai_tempi(testo))


def tempo_da_raggiungere(cartella, auto, pista):
    return carica(cartella).get(_chiave(auto, pista))


def percentuale(mio_ms, riferimento_ms):
    """Il tuo tempo rispetto al riferimento, in % (100 = pari; più alto = più lento)."""
    if not mio_ms or not riferimento_ms:
        return None
    return round(mio_ms * 100.0 / riferimento_ms, 1)


def stato(cartella, auto, pista, mio_migliore_ms):
    c = tempo_da_raggiungere(cartella, auto, pista)
    if not c:
        return None
    out = dict(c)
    out["mio_ms"] = mio_migliore_ms
    out["pct_primo"] = percentuale(mio_migliore_ms, c["primo_ms"])
    out["pct_mediana"] = percentuale(mio_migliore_ms, c["mediana_ms"])
    out["pct_ultimo"] = percentuale(mio_migliore_ms, c["ultimo_ms"])
    out["testo"] = frase(out)
    return out


def frase(s):
    if not s.get("mio_ms"):
        return "Tempo da raggiungere: mediana %s (primo %s)." % (formatta_tempo(s["mediana_ms"]), formatta_tempo(s["primo_ms"]))
    liv = "sotto l'ultimo" if s["mio_ms"] > s["ultimo_ms"] else "tra l'ultimo e la mediana" if s["mio_ms"] > s["mediana_ms"] else "meglio della mediana"
    return "Sei al %.1f%% del primo e al %.1f%% della mediana (%s). Obiettivo: mediana %s." % (s["pct_primo"], s["pct_mediana"], liv, formatta_tempo(s["mediana_ms"]))
