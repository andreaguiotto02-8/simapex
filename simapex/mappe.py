# -*- coding: utf-8 -*-
"""Note sulle mappe motore: per ogni auto Claude cerca online cosa fa ciascuna mappa e quando usarla.
Il risultato si salva sul PC (una volta per auto) e non cambia nulla nel gioco: sono solo consigli."""
import json
import os
import re
import time

from . import assistente, claude_api

STRUMENTO_WEB = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 4}]

SISTEMA = (
    "Sei un ingegnere di pista esperto di Assetto Corsa Competizione (ACC). Rispondi SOLO con un oggetto JSON valido, in italiano semplice, senza testo fuori dal JSON. "
    "Non inventare: se non trovi informazioni affidabili su cosa fa ciascuna mappa motore di quell'auto, scrivilo e metti affidabilita \"bassa\". "
    "Formato: {\"auto\": nome leggibile, \"mappe\": [{\"numero\": 1, \"cosa_fa\": \"...\"}], "
    "\"mappa_giri_costanti\": numero o null, \"mappa_spinta\": numero o null, "
    "\"quando_spingere\": \"frase breve\", \"quando_passo_costante\": \"frase breve\", "
    "\"come_si_cambia\": \"frase breve\", \"affidabilita\": \"alta\"|\"media\"|\"bassa\", \"nota\": \"limiti o dubbi\"}. "
    "Ogni frase al massimo 25 parole. Le mappe sono solo suggerimenti per il pilota, che le cambia da solo."
)


def _cartella(dati):
    c = os.path.join(dati, "mappe")
    os.makedirs(c, exist_ok=True)
    return c


def _file(dati, auto):
    return os.path.join(_cartella(dati), re.sub(r"[^a-zA-Z0-9_.-]", "_", auto) + ".json")


def leggi(dati, auto):
    try:
        with open(_file(dati, auto), "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _numero(x):
    try:
        n = int(x)
        return n if 1 <= n <= 20 else None
    except (TypeError, ValueError):
        return None


def pulisci(r):
    """Tiene solo i campi attesi, con testi corti."""
    def t(x, n=300):
        return str(x or "").strip()[:n]
    mappe = []
    for m in (r.get("mappe") or [])[:12]:
        if isinstance(m, dict) and _numero(m.get("numero")):
            mappe.append({"numero": _numero(m["numero"]), "cosa_fa": t(m.get("cosa_fa"))})
    aff = r.get("affidabilita") if r.get("affidabilita") in ("alta", "media", "bassa") else "bassa"
    return {"auto_nome": t(r.get("auto"), 80), "mappe": mappe,
            "mappa_giri_costanti": _numero(r.get("mappa_giri_costanti")), "mappa_spinta": _numero(r.get("mappa_spinta")),
            "quando_spingere": t(r.get("quando_spingere")), "quando_passo_costante": t(r.get("quando_passo_costante")),
            "come_si_cambia": t(r.get("come_si_cambia")), "affidabilita": aff, "nota": t(r.get("nota"), 400)}


def cerca(chiave, dati, auto, log=None, chiedi=None):
    """Chiede a Claude (con ricerca sul web, se disponibile) le mappe motore dell'auto e salva la nota."""
    chiedi = chiedi or claude_api.chiedi
    domanda = ("Auto di ACC (nome interno): %s. Cerca online cosa fa ciascuna mappa motore (engine map) di questa auto in ACC "
               "(potenza, erogazione, consumo) e dimmi quale usare per giri a passo costante e quale per spingere al massimo (qualifica / attacco)." % auto)
    online = True
    try:
        testo, uso = chiedi(chiave, domanda, sistema=SISTEMA, max_token=2500, tempo_max=120, strumenti=STRUMENTO_WEB)
    except RuntimeError as e:
        if "rifiutata" not in str(e):
            raise
        if log:
            log("mappe: ricerca web non disponibile (%s), riprovo senza" % e)
        online = False
        testo, uso = chiedi(chiave, domanda, sistema=SISTEMA, max_token=2000, tempo_max=60)
    r = pulisci(assistente.estrai_json(testo))
    r.update({"auto": auto, "ricerca_online": online, "fonti": uso.get("fonti", []), "ora": time.strftime("%Y-%m-%d %H:%M")})
    if not online and r["affidabilita"] == "alta":
        r["affidabilita"] = "media"
    tmp = _file(dati, auto) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=2)
    os.replace(tmp, _file(dati, auto))
    return r
