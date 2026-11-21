# -*- coding: utf-8 -*-
"""Aggiornamento automatico: all'avvio scarica la versione più recente e si riapre da solo."""
import os
import subprocess
import sys
import urllib.request

from . import invio


def _exe():
    return sys.executable if getattr(sys, "frozen", False) else None


def pulisci_vecchi():
    e = _exe()
    if e:
        try:
            os.remove(e + ".vecchio")
        except OSError:
            pass


def _scarica(url, dest, tempo_max=90):
    req = urllib.request.Request(url, headers={"User-Agent": "Simapex"})
    with urllib.request.urlopen(req, timeout=tempo_max) as r, open(dest, "wb") as f:
        while True:
            blocco = r.read(1 << 16)
            if not blocco:
                break
            f.write(blocco)
    ok = os.path.getsize(dest) > 3_000_000
    if ok:
        with open(dest, "rb") as f:
            ok = f.read(2) == b"MZ"
    return ok


def prova(versione, log=lambda t: None, inizio=None, prima_di_riavviare=None):
    """True se ha installato una versione nuova e ha riavviato il programma (chi chiama deve uscire)."""
    e = _exe()
    if not e or os.environ.get("SIMAPEX_NO_AGG") or os.environ.get("SIMAPEX_APPENA_AGGIORNATO"):
        return False
    try:
        info = invio.controlla_aggiornamenti(versione)
        if not info.get("disponibile"):
            return False
        log("aggiornamento da %s a %s" % (versione, info.get("ultima")))
        if inizio:
            inizio(info.get("ultima"))
        nuovo = e + ".nuovo"
        if not _scarica(info["scarica"], nuovo):
            try:
                os.remove(nuovo)
            except OSError:
                pass
            log("download non valido, resto sulla versione attuale")
            return False
        os.replace(e, e + ".vecchio")
        try:
            os.replace(nuovo, e)
        except OSError:
            os.replace(e + ".vecchio", e)
            raise
        if prima_di_riavviare:
            prima_di_riavviare()  # libera la porta prima che parta la versione nuova
        amb = dict(os.environ)
        amb["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
        amb["SIMAPEX_APPENA_AGGIORNATO"] = "1"
        subprocess.Popen([e], env=amb, close_fds=True,
                         creationflags=0x00000008 | 0x00000200)  # DETACHED_PROCESS | NEW_PROCESS_GROUP
        return True
    except Exception as ex:
        log("aggiornamento non riuscito: %s" % ex)
        return False
