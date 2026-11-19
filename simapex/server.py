# -*- coding: utf-8 -*-
import json
import os
import sys
import threading
import time
import traceback
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .setup_acc import elenco_setup
from .telemetria import Lettore
from .ui import PAGINA
from .versione import VERSIONE

PORTA = 8765
_ultima_richiesta = [time.time()]
_lettore = Lettore()
_fermati = threading.Event()


def cartella_dati():
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    p = os.path.join(base, "Simapex")
    os.makedirs(p, exist_ok=True)
    return p


def scrivi_log(testo):
    try:
        with open(os.path.join(cartella_dati(), "log.txt"), "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + testo + "\n")
    except Exception:
        pass


class Gestore(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _invia(self, codice, corpo, tipo):
        b = corpo.encode("utf-8")
        self.send_response(codice)
        self.send_header("Content-Type", tipo + "; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        _ultima_richiesta[0] = time.time()
        try:
            if self.path in ("/", "/index.html"):
                self._invia(200, PAGINA.replace("__VERSIONE__", VERSIONE), "text/html")
            elif self.path.startswith("/api/stato"):
                d = _lettore.stato()
                d["versione"] = VERSIONE
                self._invia(200, json.dumps(d), "application/json")
            elif self.path.startswith("/api/setup"):
                self._invia(200, json.dumps(elenco_setup()), "application/json")
            else:
                self._invia(404, "non trovato", "text/plain")
        except Exception:
            scrivi_log(traceback.format_exc())
            self._invia(500, "errore", "text/plain")

    def do_POST(self):
        _ultima_richiesta[0] = time.time()
        if self.path == "/api/chiudi":
            self._invia(200, "{}", "application/json")
            _fermati.set()
        else:
            self._invia(404, "non trovato", "text/plain")


def _guardiano():
    # se il browser viene chiuso e non arrivano più richieste, il programma si chiude da solo
    while not _fermati.is_set():
        time.sleep(2)
        if time.time() - _ultima_richiesta[0] > 45:
            _fermati.set()


def main(apri_browser=True):
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", PORTA), Gestore)
    except OSError:
        # già aperto: si mostra solo la pagina
        if apri_browser:
            webbrowser.open("http://127.0.0.1:%d/" % PORTA)
        return
    scrivi_log("avviato versione " + VERSIONE)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    threading.Thread(target=_guardiano, daemon=True).start()
    if apri_browser:
        webbrowser.open("http://127.0.0.1:%d/" % PORTA)
    _fermati.wait()
    srv.shutdown()
    scrivi_log("chiuso")
