# -*- coding: utf-8 -*-
"""Invio dei risultati delle prove a Claude (deposito privato su GitHub) e controllo aggiornamenti."""
import base64
import json
import os
import time
import urllib.error
import urllib.request

DEPOSITO_PREDEFINITO = "andreaguiotto02-8/simapex-data"
DEPOSITO_PROGRAMMA = "andreaguiotto02-8/simapex"
TEMPO_MAX = 20


def base_api():
    return os.environ.get("SIMAPEX_GH_API", "https://api.github.com")


def _richiesta(metodo, url, token=None, corpo=None):
    h = {"Accept": "application/vnd.github+json", "User-Agent": "Simapex"}
    if token:
        h["Authorization"] = "Bearer " + token
    dati = None
    if corpo is not None:
        dati = json.dumps(corpo).encode("utf-8")
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=dati, headers=h, method=metodo)
    try:
        with urllib.request.urlopen(req, timeout=TEMPO_MAX) as r:
            return r.status, json.loads(r.read().decode("utf-8") or "null")
    except urllib.error.HTTPError as e:
        return e.code, None
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        if "timed out" in str(e).lower():
            raise RuntimeError("tempo scaduto: GitHub non risponde (oltre 20 secondi). Riprova tra poco.")
        raise RuntimeError("nessuna connessione a internet o GitHub non raggiungibile.")


def carica_file(repo, token, percorso, testo, messaggio):
    url = "%s/repos/%s/contents/%s" % (base_api(), repo, percorso)
    codice, info = _richiesta("GET", url, token)
    sha = None
    if codice == 200 and isinstance(info, dict):
        sha = info.get("sha")
    elif codice == 401:
        raise RuntimeError("la chiave non è valida o è scaduta.")
    elif codice not in (404,):
        if codice == 403:
            raise RuntimeError("la chiave non ha i permessi giusti.")
        raise RuntimeError("GitHub ha risposto con l'errore %s." % codice)
    corpo = {"message": messaggio, "content": base64.b64encode(testo.encode("utf-8")).decode("ascii")}
    if sha:
        corpo["sha"] = sha
    codice, _ = _richiesta("PUT", url, token, corpo)
    if codice not in (200, 201):
        if codice == 401:
            raise RuntimeError("la chiave non è valida o è scaduta.")
        if codice in (403, 404):
            raise RuntimeError("la chiave non ha il permesso di scrivere nel deposito dei dati.")
        raise RuntimeError("GitHub ha risposto con l'errore %s." % codice)


def invia_risultati(repo, token, pacchetto, diagnostica):
    ora = time.strftime("%Y-%m-%d_%H%M%S")
    carica_file(repo, token, "pc/prove/%s.json" % ora, json.dumps(pacchetto, ensure_ascii=False, indent=1), "prove dal PC " + ora)
    carica_file(repo, token, "pc/diag.json", json.dumps(diagnostica, ensure_ascii=False, indent=1), "diagnostica PC " + ora)
    return ora


def _versione_tupla(v):
    out = []
    for p in str(v).lstrip("v").split("."):
        try:
            out.append(int(p))
        except ValueError:
            out.append(0)
    return tuple(out)


def controlla_aggiornamenti(versione_attuale):
    codice, info = _richiesta("GET", "%s/repos/%s/releases/latest" % (base_api(), DEPOSITO_PROGRAMMA))
    if codice != 200 or not isinstance(info, dict):
        return {"disponibile": False}
    nuova = str(info.get("tag_name", "")).lstrip("v")
    return {
        "disponibile": _versione_tupla(nuova) > _versione_tupla(versione_attuale),
        "ultima": nuova,
        "scarica": "https://github.com/%s/releases/latest/download/Simapex.exe" % DEPOSITO_PROGRAMMA,
    }
