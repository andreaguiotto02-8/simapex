# -*- coding: utf-8 -*-
import json
import os
import sys
import threading
import time
import traceback
import subprocess
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import aggiorna, claude_api, invio
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


def _file_impostazioni():
    return os.path.join(cartella_dati(), "impostazioni.json")


def carica_impostazioni():
    try:
        with open(_file_impostazioni(), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def salva_impostazioni(d):
    with open(_file_impostazioni(), "w", encoding="utf-8") as f:
        json.dump(d, f)


def coda_log(n=40):
    try:
        with open(os.path.join(cartella_dati(), "log.txt"), "r", encoding="utf-8") as f:
            return f.read().splitlines()[-n:]
    except Exception:
        return []


def scrivi_log(testo):
    try:
        with open(os.path.join(cartella_dati(), "log.txt"), "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + testo + "\n")
    except Exception:
        pass


def percorso_icona(nome):
    if getattr(sys, "frozen", False):
        base = os.path.join(sys._MEIPASS, "simapex", "icone")
    else:
        base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icone")
    return os.path.join(base, nome)


MANIFEST = {
    "name": "Simapex", "short_name": "Simapex", "description": "Il team intorno al pilota",
    "start_url": "/", "scope": "/", "display": "standalone",
    "background_color": "#0e1116", "theme_color": "#0e1116",
    "icons": [
        {"src": "/icona-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
        {"src": "/icona-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
    ],
}
SW_MINIMO = "self.addEventListener('install',e=>self.skipWaiting());self.addEventListener('activate',e=>e.waitUntil(self.clients.claim()));self.addEventListener('fetch',()=>{});"


def apri_finestra(url):
    """Apre Simapex come finestra di programma (senza schede del browser), con la sua icona.
    Se non trova Edge o Chrome, usa il browser normale."""
    if sys.platform.startswith("win"):
        pf = os.environ.get("ProgramFiles", "C:\\Program Files")
        pf86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
        loc = os.environ.get("LOCALAPPDATA", "")
        candidati = [
            os.path.join(pf86, "Microsoft", "Edge", "Application", "msedge.exe"),
            os.path.join(pf, "Microsoft", "Edge", "Application", "msedge.exe"),
            os.path.join(pf, "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(pf86, "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(loc, "Google", "Chrome", "Application", "chrome.exe"),
        ]
        for c in candidati:
            if c and os.path.isfile(c):
                try:
                    subprocess.Popen([c, "--app=" + url, "--window-size=1100,900"])
                    return
                except Exception:
                    scrivi_log(traceback.format_exc())
    webbrowser.open(url)


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

    def _invia_file(self, nome, tipo):
        with open(percorso_icona(nome), "rb") as f:
            b = f.read()
        self.send_response(200)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "max-age=3600")
        self.end_headers()
        self.wfile.write(b)

    def _corpo_json(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0 or n > 2000000:
            return {}
        return json.loads(self.rfile.read(n).decode("utf-8"))

    def do_GET(self):
        _ultima_richiesta[0] = time.time()
        try:
            if self.path in ("/", "/index.html"):
                self._invia(200, PAGINA.replace("__VERSIONE__", VERSIONE), "text/html")
            elif self.path == "/manifest.webmanifest":
                self._invia(200, json.dumps(MANIFEST), "application/manifest+json")
            elif self.path == "/sw.js":
                self._invia(200, SW_MINIMO, "text/javascript")
            elif self.path == "/icona-192.png":
                self._invia_file("icona-192.png", "image/png")
            elif self.path == "/icona-512.png":
                self._invia_file("icona-512.png", "image/png")
            elif self.path == "/favicon.ico":
                self._invia_file("icona.ico", "image/x-icon")
            elif self.path.startswith("/api/stato"):
                d = _lettore.stato()
                d["versione"] = VERSIONE
                d["invio_configurato"] = bool(carica_impostazioni().get("gh_token"))
                d["claude_configurato"] = bool(carica_impostazioni().get("claude_key"))
                self._invia(200, json.dumps(d), "application/json")
            elif self.path.startswith("/api/aggiornamenti"):
                try:
                    r = invio.controlla_aggiornamenti(VERSIONE)
                except Exception:
                    r = {"disponibile": False}
                self._invia(200, json.dumps(r), "application/json")
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
        elif self.path == "/api/chiave":
            try:
                d = self._corpo_json()
                t = str(d.get("token", "")).strip()
                if not t:
                    self._invia(400, json.dumps({"ok": False, "errore": "La chiave è vuota."}), "application/json")
                    return
                imp = carica_impostazioni()
                imp["gh_token"] = t
                imp.setdefault("gh_repo", invio.DEPOSITO_PREDEFINITO)
                salva_impostazioni(imp)
                self._invia(200, json.dumps({"ok": True}), "application/json")
            except Exception:
                scrivi_log(traceback.format_exc())
                self._invia(500, json.dumps({"ok": False, "errore": "Non sono riuscito a salvare la chiave."}), "application/json")
        elif self.path == "/api/claude-chiave":
            try:
                t = str(self._corpo_json().get("chiave", "")).strip()
                if not t.startswith("sk-ant-"):
                    self._invia(200, json.dumps({"ok": False, "errore": "Quella non sembra la chiave giusta: deve iniziare con sk-ant-"}), "application/json")
                    return
                imp = carica_impostazioni()
                imp["claude_key"] = t
                salva_impostazioni(imp)
                self._invia(200, json.dumps({"ok": True}), "application/json")
            except Exception:
                scrivi_log(traceback.format_exc())
                self._invia(200, json.dumps({"ok": False, "errore": "Non sono riuscito a salvare la chiave."}), "application/json")
        elif self.path == "/api/claude-prova":
            try:
                k = carica_impostazioni().get("claude_key")
                if not k:
                    self._invia(200, json.dumps({"ok": False, "errore": "Manca la chiave."}), "application/json")
                    return
                testo, uso = claude_api.chiedi(k, "Rispondi in italiano con una sola frase breve: sei pronto ad aiutare un pilota di simulatori a sistemare il setup?", claude_api.MODELLO_PROVA, max_token=60)
                self._invia(200, json.dumps({"ok": True, "risposta": testo, "token": uso}), "application/json")
            except RuntimeError as e:
                self._invia(200, json.dumps({"ok": False, "errore": str(e)}), "application/json")
            except Exception:
                scrivi_log(traceback.format_exc())
                self._invia(200, json.dumps({"ok": False, "errore": "Errore imprevisto."}), "application/json")
        elif self.path == "/api/invia":
            try:
                imp = carica_impostazioni()
                if not imp.get("gh_token"):
                    self._invia(200, json.dumps({"ok": False, "errore": "Manca la chiave di accesso."}), "application/json")
                    return
                pacchetto = self._corpo_json()
                automatico = bool(pacchetto.pop("automatico", False))
                pacchetto["versione_programma"] = VERSIONE
                diag = {"versione": VERSIONE, "ora": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "stato_attuale": _lettore.stato(), "setup": elenco_setup(), "log": coda_log()}
                ora = invio.invia_risultati(imp.get("gh_repo", invio.DEPOSITO_PREDEFINITO), imp["gh_token"], pacchetto, diag, automatico)
                self._invia(200, json.dumps({"ok": True, "ora": ora}), "application/json")
            except RuntimeError as e:
                self._invia(200, json.dumps({"ok": False, "errore": str(e)}), "application/json")
            except Exception:
                scrivi_log(traceback.format_exc())
                self._invia(200, json.dumps({"ok": False, "errore": "Errore imprevisto durante l'invio."}), "application/json")
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
            apri_finestra("http://127.0.0.1:%d/" % PORTA)
        return
    scrivi_log("avviato versione " + VERSIONE)
    aggiorna.pulisci_vecchi()
    if apri_browser and aggiorna.prova(VERSIONE, scrivi_log):
        srv.server_close()
        return
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    threading.Thread(target=_guardiano, daemon=True).start()
    if apri_browser:
        apri_finestra("http://127.0.0.1:%d/" % PORTA)
    _fermati.wait()
    srv.shutdown()
    scrivi_log("chiuso")
