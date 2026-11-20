# -*- coding: utf-8 -*-
"""Chiamate all'API di Claude (a pagamento, chiave personale salvata solo sul PC)."""
import json
import os
import urllib.error
import urllib.request

MODELLO_PROVA = "claude-haiku-5-5"
MODELLO = "claude-sonnet-5-5"
TEMPO_MAX = 40


def _url():
    return os.environ.get("SIMAPEX_CLAUDE_API", "https://api.anthropic.com") + "/v1/messages"


def chiedi(chiave, domanda, modello=MODELLO, sistema=None, max_token=600):
    corpo = {"model": modello, "max_tokens": max_token,
             "messages": [{"role": "user", "content": domanda}]}
    if sistema:
        corpo["system"] = sistema
    req = urllib.request.Request(_url(), data=json.dumps(corpo).encode("utf-8"), method="POST", headers={
        "x-api-key": chiave, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TEMPO_MAX) as r:
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
    uso = d.get("usage", {})
    return testo, uso
