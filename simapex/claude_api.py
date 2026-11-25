# -*- coding: utf-8 -*-
"""Chiamate all'API di Claude (a pagamento, chiave personale salvata solo sul PC)."""
import json
import os
import urllib.error
import urllib.request

MODELLO_PROVA = "claude-haiku-5-5"
MODELLO = "claude-sonnet-5-5"
TEMPO_MAX = 40
PRIMA = None   # funzione() che può bloccare la chiamata (limite mensile)
SU_USO = None   # funzione(modello, uso) chiamata dopo ogni risposta, per contare il costo
# Prezzi stimati in dollari per milione di token (entrata, uscita) e per ricerca web
PREZZI = {"claude-haiku-5-5": (1.0, 5.0), "claude-sonnet-5-5": (3.0, 15.0)}
PREZZO_RICERCA = 0.01


def costo_uso(modello, uso):
    pi, po = PREZZI.get(modello, (3.0, 15.0))
    ric = ((uso or {}).get("server_tool_use") or {}).get("web_search_requests", 0) or 0
    return ((uso or {}).get("input_tokens", 0) * pi + (uso or {}).get("output_tokens", 0) * po) / 1e6 + ric * PREZZO_RICERCA


def _url():
    return os.environ.get("SIMAPEX_CLAUDE_API", "https://api.anthropic.com") + "/v1/messages"


def chiedi(chiave, domanda, modello=MODELLO, sistema=None, max_token=600, tempo_max=None, strumenti=None):
    if PRIMA:
        PRIMA()
    corpo = {"model": modello, "max_tokens": max_token,
             "messages": [{"role": "user", "content": domanda}]}
    if sistema:
        corpo["system"] = sistema
    if strumenti:
        corpo["tools"] = strumenti
    req = urllib.request.Request(_url(), data=json.dumps(corpo).encode("utf-8"), method="POST", headers={
        "x-api-key": chiave, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=tempo_max or TEMPO_MAX) as r:
            d = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 401:
            raise RuntimeError("la chiave non è valida: controlla di averla copiata tutta.")
        if e.code == 403:
            raise RuntimeError("la chiave non ha il permesso di usare Claude.")
        if e.code == 429:
            raise RuntimeError("troppe richieste in poco tempo: riprova tra un minuto.")
        if e.code in (400, 402):
            try:
                msg = json.loads(e.read().decode("utf-8")).get("error", {}).get("message", "")
            except Exception:
                msg = ""
            if "credit" in msg.lower() or e.code == 402:
                raise RuntimeError("il credito è finito: ricarica dal sito dell'API.")
            raise RuntimeError("richiesta rifiutata (%s)." % (msg or e.code))
        raise RuntimeError("il servizio di Claude ha risposto con l'errore %s." % e.code)
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        if "timed out" in str(e).lower():
            raise RuntimeError("Claude non risponde (oltre 40 secondi). Riprova tra poco.")
        raise RuntimeError("nessuna connessione a internet.")
    testo = "".join(b.get("text", "") for b in d.get("content", []) if b.get("type") == "text")
    uso = dict(d.get("usage", {}))
    uso["stop_reason"] = d.get("stop_reason")
    try:
        if SU_USO:
            SU_USO(modello, dict(uso))
    except Exception:
        pass
    fonti = []
    for b in d.get("content", []):
        if b.get("type") == "web_search_tool_result" and isinstance(b.get("content"), list):
            for r in b["content"]:
                if r.get("url") and r["url"] not in fonti:
                    fonti.append(r["url"])
    uso["fonti"] = fonti[:8]
    return testo, uso
