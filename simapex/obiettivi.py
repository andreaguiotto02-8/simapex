# -*- coding: utf-8 -*-
"""Percorso a obiettivi per imparare una pista: ogni sessione ha UN obiettivo misurabile e a fine sessione si dice se è raggiunto."""
import json
import os
import time

from .telemetria import formatta_tempo

NOMI_FASE = {1: "Impara il tracciato", 2: "Una curva da migliorare", 3: "Giri veloci"}
MIN_GIRI_VALUTAZIONE = 3


def _pulito(g, migliore):
    return g["tempo_ms"] <= migliore * 1.07 and len(g.get("blocchi") or []) <= 1


def giri_di(giri, auto, pista):
    return sorted((x for x in giri if x.get("auto") == auto and x.get("pista") == pista and x.get("tempo_ms")), key=lambda x: x.get("ts") or 0)


def serie_pulita(giri_sessione, migliore):
    """Il più lungo gruppo di giri puliti di fila."""
    best = cur = 0
    for g in giri_sessione:
        cur = cur + 1 if _pulito(g, migliore) else 0
        best = max(best, cur)
    return best


def nuovo(fase, giri_pista, perdita=None):
    """Obiettivo per la fase data. perdita = (indice_tratto, ms persi rispetto al giro migliore) se disponibile."""
    tempi = [g["tempo_ms"] for g in giri_pista]
    best = min(tempi) if tempi else None
    o = {"fase": fase, "titolo": NOMI_FASE[fase], "creato": time.time(), "base_ms": best}
    if fase == 1:
        o.update(tipo="serie", n=5, testo="Fai 5 giri puliti di fila, senza fretta. Impara dove va la pista.")
    elif fase == 2:
        if perdita and perdita[1] >= 20:
            o.update(tipo="tratto", tratto=perdita[0], perdita_ms=perdita[1],
                     testo="Migliora una sola parte del giro (tratto %d di 25: ci perdi %.1f s). Il resto lascialo com'è." % (perdita[0] + 1, perdita[1] / 1000.0))
        else:
            o.update(tipo="migliora", ms=300, testo="Abbassa il tuo giro migliore di 3 decimi (%s)." % (formatta_tempo(best - 300) if best else "?"))
    else:
        o.update(tipo="vicini", n=3, pct=0.7, testo="Fai 3 giri entro lo 0,7% dal tuo migliore (%s). Poche frasi radio, solo giri veloci." % (formatta_tempo(best * 1.007) if best else "?"))
    return o


def valuta(o, giri_dopo, giri_prima, perdita_attuale=None):
    """(raggiunto, frase, valutabile). giri_dopo = giri fatti dopo la creazione dell'obiettivo; giri_prima = giri precedenti."""
    if len(giri_dopo) < MIN_GIRI_VALUTAZIONE:
        return False, "", False
    migliore = min([g["tempo_ms"] for g in giri_prima + giri_dopo])
    t = o.get("tipo")
    if t == "serie":
        s = serie_pulita(giri_dopo, migliore)
        ok = s >= o["n"]
        return ok, ("Obiettivo raggiunto: %d giri puliti di fila." % s) if ok else "Non ancora: al massimo %d giri puliti di fila su %d." % (s, o["n"]), True
    if t == "tratto":
        if perdita_attuale is None:
            return False, "", False
        ok = perdita_attuale <= max(20, o["perdita_ms"] / 2.0)
        return ok, ("Obiettivo raggiunto: nel tratto ora perdi %.1f s (prima %.1f)." % (perdita_attuale / 1000.0, o["perdita_ms"] / 1000.0)) if ok else \
            "Non ancora: nel tratto perdi %.1f s (prima %.1f)." % (perdita_attuale / 1000.0, o["perdita_ms"] / 1000.0), True
    if t == "migliora":
        prima = min([g["tempo_ms"] for g in giri_prima] or [o["base_ms"] or 10 ** 9])
        d = prima - min(g["tempo_ms"] for g in giri_dopo)
        ok = d >= o["ms"]
        return ok, ("Obiettivo raggiunto: migliorato di %.1f s." % (d / 1000.0)) if ok else "Non ancora: %s di %.1f s sul tuo migliore." % ("migliorato" if d > 0 else "peggiorato", abs(d) / 1000.0), True
    if t == "vicini":
        riferimento = o.get("base_ms") or migliore
        vicini = [g for g in giri_dopo if g["tempo_ms"] <= riferimento * (1 + o["pct"] / 100.0) and len(g.get("blocchi") or []) <= 1]
        ok = len(vicini) >= o["n"]
        return ok, ("Obiettivo raggiunto: %d giri veloci vicini al tuo migliore." % len(vicini)) if ok else "Non ancora: %d giri vicini al tuo migliore su %d." % (len(vicini), o["n"]), True
    return False, "", False


def _file(cartella):
    return os.path.join(cartella, "obiettivi.json")


def carica(cartella):
    try:
        with open(_file(cartella), "r", encoding="utf-8") as f:
            d = json.load(f)
            return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def salva(cartella, d):
    try:
        with open(_file(cartella), "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False)
    except Exception:
        pass


def stato(cartella, giri, auto, pista, perdita_fn=None):
    """Obiettivo attuale per auto/pista; se l'ultima sessione lo ha chiuso, scrive l'esito e passa al successivo.
    perdita_fn(giri_sessione) -> (tratto, ms persi) o None, usata nelle fasi 2."""
    if not auto or not pista:
        return None
    tutti = carica(cartella)
    k = "%s|%s" % (auto, pista)
    rec = tutti.get(k) or {}
    gp = giri_di(giri, auto, pista)
    o = rec.get("obiettivo")
    if not o:
        if not gp:
            return {"fase": 1, "titolo": NOMI_FASE[1], "testo": "Fai 5 giri puliti di fila, senza fretta. Impara dove va la pista.", "esito": rec.get("esito", ""), "raggiunto": None}
        o = nuovo(1, gp)
        rec = {"obiettivo": o, "esito": rec.get("esito", "")}
    dopo = [g for g in gp if (g.get("ts") or 0) > o["creato"]]
    prima = [g for g in gp if (g.get("ts") or 0) <= o["creato"]]
    att = None
    if perdita_fn and o.get("tipo") == "tratto" and dopo:
        try:
            p = perdita_fn(dopo)
            if p and p[0] == o["tratto"]:
                att = p[1]
            elif p is not None:
                att = 0
        except Exception:
            att = None
    ok, frase, valutabile = valuta(o, dopo, prima, att)
    if valutabile:
        rec["esito"] = frase
        if ok:
            f = min(3, o["fase"] + 1) if o["fase"] < 3 else 3
            perd = None
            if f == 2 and perdita_fn:
                try:
                    perd = perdita_fn(dopo)
                except Exception:
                    perd = None
            rec["obiettivo"] = o = nuovo(f, gp, perd)
        # non raggiunto: resta lo stesso obiettivo, ma si riparte a contare dalle sessioni successive
        else:
            o["creato"] = max((g.get("ts") or 0) for g in dopo)
    tutti[k] = rec
    salva(cartella, tutti)
    return {"fase": o["fase"], "titolo": o["titolo"], "testo": o["testo"], "esito": rec.get("esito", ""), "raggiunto": ok if valutabile else None}
