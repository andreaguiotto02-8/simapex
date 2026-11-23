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

from . import aggiorna, assistente, assistente_f1, claude_api, invio
from . import circuito, esito, f1, ingegnere, mappe, pressioni, ptt, tracce
from .report import crea_report, dettaglio_sessione, elenco_sessioni, tutte_le_sessioni, ultima_sessione
from .stile import RegistroStile, ruota_bloccata
from .setup_acc import contenuti_setup, elenco_setup, trova_cartella_setup
from .telemetria import Lettore
from .versione import VERSIONE

PORTA = 8765
_ultima_richiesta = [time.time()]
_lettore = f1.LettoreMulti(Lettore(), f1.LettoreF1(log=lambda m: scrivi_log(m)))
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


def _file_quaderno():
    return os.path.join(cartella_dati(), "quaderno.json")


def carica_quaderno():
    try:
        with open(_file_quaderno(), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def salva_quaderno(q):
    with open(_file_quaderno(), "w", encoding="utf-8") as f:
        json.dump(q, f, ensure_ascii=False, indent=1)


_gomme = {"auto": None, "pista": None, "n": 0, "p": [0.0] * 4, "t": [0.0] * 4, "tmax": [0.0] * 4, "z": [[0.0] * 4 for _ in range(3)], "nz": 0}


def campiona_gomme(d):
    """Accumula pressioni e temperature gomme mentre l'auto si muove (media sulla guida)."""
    if not d.get("collegato") or (d.get("velocita") or 0) < 60:
        return
    if (d.get("auto"), d.get("pista")) != (_gomme["auto"], _gomme["pista"]):
        _gomme.update(auto=d.get("auto"), pista=d.get("pista"), n=0, p=[0.0] * 4, t=[0.0] * 4, tmax=[0.0] * 4, z=[[0.0] * 4 for _ in range(3)], nz=0)
    pr, te = d.get("pressioni") or [], d.get("temp_gomme") or []
    if len(pr) != 4 or len(te) != 4:
        return
    _gomme["n"] += 1
    for i in range(4):
        _gomme["p"][i] += pr[i]
        _gomme["t"][i] += te[i]
        _gomme["tmax"][i] = max(_gomme["tmax"][i], te[i])
    z = d.get("temp_zone")
    if z and all(len(z.get(k, [])) == 4 for k in ("interna", "centro", "esterna")):
        _gomme["nz"] += 1
        for j, k in enumerate(("interna", "centro", "esterna")):
            for i in range(4):
                _gomme["z"][j][i] += z[k][i]


def riepilogo_gomme():
    n = _gomme["n"]
    if n < 30:
        return None
    nomi = ["ant_sx", "ant_dx", "post_sx", "post_dx"]
    return {"secondi_di_guida": n,
            "pressione_media_psi": {nomi[i]: round(_gomme["p"][i] / n, 1) for i in range(4)},
            "temperatura_media_C": {nomi[i]: round(_gomme["t"][i] / n) for i in range(4)},
            "temperatura_max_C": {nomi[i]: round(_gomme["tmax"][i]) for i in range(4)},
            "temperatura_zone_C": ({nomi[i]: {k: round(_gomme["z"][j][i] / _gomme["nz"])
                                              for j, k in enumerate(("interna", "centro", "esterna"))}
                                    for i in range(4)} if _gomme["nz"] >= 30 else None)}


_stile = [None]


def aggiorna_esiti():
    try:
        q = carica_quaderno()
        if esito.aggiorna(q, registro_stile().giri):
            salva_quaderno(q)
    except Exception:
        pass


def registro_stile():
    if _stile[0] is None:
        _stile[0] = RegistroStile(os.path.join(cartella_dati(), "stile.json"))
    return _stile[0]


def _carica_pista_online(pista, t):
    """Condivide il disegno appena registrato (se la chiave di invio è configurata)."""
    try:
        tok = carica_impostazioni().get("gh_token")
        if tok:
            invio.carica_file(invio.DEPOSITO_PREDEFINITO, tok, "pc/piste/%s.json" % circuito.nome_file(pista),
                              json.dumps(t), "disegno pista " + str(pista))
    except Exception:
        pass


_tr = [None]


def tracce_giri():
    if _tr[0] is None:
        _tr[0] = tracce.Tracce(os.path.join(cartella_dati(), "tracce"))
    return _tr[0]


_blocco = {"t": 0.0, "ruota": None}


def consumo_per_giro(auto, pista):
    g = [x for x in registro_stile().giri if x["auto"] == auto and x["pista"] == pista and x.get("carburante") is not None][-4:]
    d = [g[i - 1]["carburante"] - g[i]["carburante"] for i in range(1, len(g)) if g[i].get("ts", 0) - g[i - 1].get("ts", 0) < 600]
    d = [x for x in d if x > 0]
    return round(sum(d) / len(d), 2) if d else None


_tastiera = ptt.Tastiera()
_ptt = ptt.Ptt(carica_impostazioni().get("ptt_tasto", 25), azioni=carica_impostazioni().get("tasti_azioni", {}))


FUNZIONI_OK_DI_PARTENZA = ("apre", "setup", "acc", "giri", "mappa", "base", "carica", "guida1", "blocchi", "gomme", "delta", "carburante", "sessioni", "dettaglio", "confronto", "esito")


def funzioni():
    f = dict(carica_impostazioni().get("funzioni") or {})
    for k in FUNZIONI_OK_DI_PARTENZA:
        f.setdefault(k, {"s": "ok", "n": ""})
    return f


_box = [None]
_cache_box = {}


_proc = {"t": 0, "v": ""}


def gioco_aperto():
    """Nome del gioco aperto sul PC (F1 25 o ACC), anche se non manda ancora dati. Solo Windows."""
    if not sys.platform.startswith("win"):
        return ""
    if time.time() - _proc["t"] < 5:
        return _proc["v"]
    _proc["t"] = time.time()
    try:
        out = subprocess.run(["tasklist", "/FO", "CSV", "/NH"], capture_output=True, text=True, timeout=4,
                             creationflags=0x08000000).stdout.lower()
        _proc["v"] = "F1 25" if "f1_25.exe" in out else ("ACC" if "ac2-win64-shipping.exe" in out else "")
    except Exception:
        _proc["v"] = ""
    return _proc["v"]


def box_corsia():
    if _box[0] is None:
        _box[0] = circuito.Box(os.path.join(cartella_dati(), "piste"))
    return _box[0]


_registratore = [None]


def registratore():
    if _registratore[0] is None:
        _registratore[0] = circuito.Registratore(os.path.join(cartella_dati(), "piste"),
                                                 lambda p, t: threading.Thread(target=_carica_pista_online, args=(p, t), daemon=True).start())
    return _registratore[0]


def _campionatore():
    tick = 0
    while not _fermati.is_set():
        try:
            d = _lettore.stato()
            registro_stile().alimenta(d)
            registratore().alimenta(d)
            box_corsia().alimenta(d)
            tracce_giri().alimenta(d)
            r = ruota_bloccata(d)
            if r is not None:
                _blocco.update(t=time.time(), ruota=r)
            if tick % 10 == 0:
                campiona_gomme(d)
            if tick % 300 == 150:
                aggiorna_esiti()
        except Exception:
            pass
        tick += 1
        _fermati.wait(0.1)


def _percorso_setup(rel):
    """Dal nome 'auto/pista/file' al percorso vero, solo se è nell'elenco dei setup trovati."""
    el = elenco_setup()
    for f in el["file"]:
        if "%s/%s/%s" % (f["auto"], f["pista"], f["nome"]) == rel:
            return el["cartella"], f
    return None, None


def scrivi_log(testo):
    try:
        with open(os.path.join(cartella_dati(), "log.txt"), "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + testo + "\n")
    except Exception:
        pass


def percorso_web(nome):
    if getattr(sys, "frozen", False):
        base = os.path.join(sys._MEIPASS, "simapex", "web")
    else:
        base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
    return os.path.join(base, nome)


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
                    # profilo tutto suo: così le opzioni (microfono incluso) valgono anche se Edge è già aperto
                    prof = os.path.join(loc or os.path.expanduser("~"), "Simapex", "browser")
                    os.makedirs(prof, exist_ok=True)
                    subprocess.Popen([c, "--app=" + url, "--window-size=1100,900", "--use-fake-ui-for-media-stream",
                                      "--user-data-dir=" + prof, "--no-first-run", "--no-default-browser-check"])
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

    def _invia_web(self, nome):
        with open(percorso_web(nome), "rb") as f:
            b = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ("text/css" if nome.endswith(".css") else "application/javascript") + "; charset=utf-8")
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
        if _aggiornando[0]:
            if self.path.startswith("/api/stato"):
                self._invia(200, json.dumps({"aggiornando": True}), "application/json")
            else:
                self._invia(200, SPLASH.replace("__V__", str(_aggiornando[0])), "text/html")
            return
        _ultima_richiesta[0] = time.time()
        try:
            if self.path in ("/", "/index.html"):
                with open(percorso_web("index.html"), "r", encoding="utf-8") as fh:
                    self._invia(200, fh.read().replace("__VERSIONE__", VERSIONE), "text/html")
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
                if d.get("collegato"):
                    d["delta_ms"] = tracce_giri().delta_live(d)
                    d["blocco_ruota"] = (["ant_sx", "ant_dx", "post_sx", "post_dx"][_blocco["ruota"]]
                                         if _blocco["ruota"] is not None and time.time() - _blocco["t"] < 2.5 else None)
                    cons = consumo_per_giro(d.get("auto"), d.get("pista"))
                    d["consumo_giro"] = cons
                    d["giri_stimati"] = round((d.get("carburante") or 0) / cons, 1) if cons else None
                    d["giro_attuale_ms"] = round(tracce_giri().trascorso_ms())
                    d["consiglio_guida"] = tracce_giri().consiglio
                    try:
                        k = (d.get("auto"), d.get("pista"), int(time.time() // 3))
                        if _cache_box.get("k") != k:
                            mt = tracce_giri().carica(d.get("auto"), d.get("pista")).get("migliore")
                            _cache_box.update(k=k, v=circuito.info_box(os.path.join(cartella_dati(), "piste"), d.get("pista"), d.get("auto"), mt))
                        d["box_info"] = _cache_box.get("v")
                    except Exception:
                        d["box_info"] = None
                d["funzioni"] = funzioni()
                d["ptt"] = _ptt.premuto
                d["ptt_tasto"] = _ptt.tasto
                d["ptt_visti"] = _ptt.ultimi
                d["gioco_aperto"] = gioco_aperto()
                d["tele"] = dict(_tastiera.conta)
                d["tele_acceso"] = _tastiera.acceso()
                d["tasti"] = dict(_ptt.azioni)
                d["tasti_conta"] = dict(_ptt.conta)
                d["tasti_assegna"] = _ptt.assegna
                if _ptt.assegnato:
                    imp = carica_impostazioni()
                    imp["tasti_azioni"] = dict(_ptt.azioni)
                    salva_impostazioni(imp)
                    _ptt.assegnato = None
                self._invia(200, json.dumps(d), "application/json")
            elif self.path in ("/app.css", "/app.js"):
                self._invia_web(self.path[1:])
            elif self.path.startswith("/api/mappe?"):
                from urllib.parse import unquote
                a = unquote(self.path.split("auto=")[1].split("&")[0]) if "auto=" in self.path else ""
                self._invia(200, json.dumps({"mappe": mappe.leggi(cartella_dati(), a) if a else None}), "application/json")
            elif self.path.startswith("/api/pista?"):
                from urllib.parse import unquote
                nome = unquote(self.path.split("nome=")[1].split("&")[0]) if "nome=" in self.path else ""
                t = circuito.carica_tracciato(nome, os.path.join(cartella_dati(), "piste"))
                bx = circuito.carica_box(os.path.join(cartella_dati(), "piste"), nome)
                if t and bx and bx.get("x"):
                    t = dict(t, box={"x": bx["x"], "z": bx["z"]})
                self._invia(200, json.dumps({"pista": t}), "application/json")
            elif self.path.startswith("/api/sessioni"):
                self._invia(200, json.dumps({"sessioni": elenco_sessioni(registro_stile().giri)[:50]}), "application/json")
            elif self.path.startswith("/api/sessione?"):
                from urllib.parse import parse_qs, urlparse
                q = parse_qs(urlparse(self.path).query)
                try:
                    sid = int(q.get("id", ["-1"])[0])
                except Exception:
                    sid = -1
                det = dettaglio_sessione(registro_stile().giri, sid, registro_stile().profilo())
                if det:
                    sess = tutte_le_sessioni(registro_stile().giri)
                    cur = next((x for x in sess if (x[0].get("ts") or 0) == sid), [])
                    prec = next((x for x in sess if x and x[0]["auto"] == det["auto"] and x[0]["pista"] == det["pista"]
                                 and (x[0].get("ts") or 0) < sid), [])
                    det["confronto"] = tracce.confronto_sessione(tracce_giri(), det["auto"], det["pista"], cur, prec)
                    det["giri_confronto"] = tracce.lista_giri(tracce_giri(), det["auto"], det["pista"])
                    det["riferimenti"] = tracce.lista_riferimenti(tracce_giri(), det["auto"], det["pista"])
                    for dg, lap in zip(det.get("dettaglio_giri") or [], cur):
                        tr_ = tracce._traccia_di(tracce_giri(), det["auto"], det["pista"], lap)
                        dg["k"] = tracce.chiave_giro(tr_) if tr_ else None
                    if q.get("a") and q.get("b"):
                        sc = tracce.confronto_giri(tracce_giri(), det["auto"], det["pista"], q["a"][0], q["b"][0])
                        if sc:
                            det["confronto"] = sc
                    det["blocchi_pos"] = [{"giro": x.get("giro"), "pos": b.get("pos"), "ruota": b["ruota"]}
                                          for x in cur for b in x.get("blocchi", []) if b.get("pos") is not None]
                    det["quaderno"] = [x for x in carica_quaderno() if x.get("auto") == det["auto"] and x.get("pista") == det["pista"]][-6:]
                self._invia(200, json.dumps({"sessione": det}), "application/json")
            elif self.path.startswith("/api/report"):
                self._invia(200, json.dumps({"report": crea_report(registro_stile().giri, None, registro_stile().profilo())}), "application/json")
            elif self.path.startswith("/api/aggiornamenti"):
                try:
                    r = invio.controlla_aggiornamenti(VERSIONE)
                except Exception:
                    r = {"disponibile": False}
                self._invia(200, json.dumps(r), "application/json")
            elif self.path.startswith("/api/assistente"):
                try:
                    st = _lettore.f1.stato()
                    if st.get("collegato") and st.get("setup_f1"):
                        qq = carica_quaderno()
                        mod = False
                        for v in qq:
                            if v.get("f1") and not v.get("ts_applicato") and v.get("auto") == st.get("auto") and v.get("pista") == st.get("pista") \
                                    and assistente_f1.applicato(v, st["setup_f1"]):
                                v["ts_applicato"] = int(time.time())
                                mod = True
                        if mod:
                            salva_quaderno(qq)
                except Exception:
                    scrivi_log(traceback.format_exc())
                aggiorna_esiti()
                self._invia(200, json.dumps({"gomme": riepilogo_gomme(), "quaderno": carica_quaderno()[-8:], "stile": registro_stile().profilo(), "giri_registrati": len(registro_stile().giri)}), "application/json")
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
        elif self.path == "/api/ptt":
            try:
                n = int(self._corpo_json().get("tasto", 0))
                n = n if 0 <= n <= 32 else 0
                imp = carica_impostazioni()
                imp["ptt_tasto"] = n
                salva_impostazioni(imp)
                _ptt.tasto = n
                self._invia(200, json.dumps({"ok": True}), "application/json")
            except Exception:
                self._invia(200, json.dumps({"ok": False, "errore": "Numero non valido."}), "application/json")
        elif self.path == "/api/tasti":
            try:
                c = self._corpo_json()
                a = c.get("azione")
                if c.get("togli") and a in ptt.Ptt.AZIONI:
                    _ptt.azioni.pop(a, None)
                    imp = carica_impostazioni()
                    imp["tasti_azioni"] = dict(_ptt.azioni)
                    salva_impostazioni(imp)
                    _ptt.assegna = None
                elif a in ptt.Ptt.AZIONI:
                    _ptt.assegna = a
                else:
                    _ptt.assegna = None
                self._invia(200, json.dumps({"ok": True}), "application/json")
            except Exception:
                self._invia(200, json.dumps({"ok": False}), "application/json")
        elif self.path == "/api/ingegnere":
            try:
                k = carica_impostazioni().get("claude_key")
                c = self._corpo_json()
                if not k:
                    self._invia(200, json.dumps({"ok": False, "errore": "Prima collega Claude (chiave API) nelle Impostazioni."}), "application/json")
                else:
                    r = ingegnere.rispondi(k, c.get("domanda"), c.get("dati") if isinstance(c.get("dati"), dict) else {}, bool(c.get("piano")))
                    self._invia(200, json.dumps({"ok": True, "risposta": r}), "application/json")
            except RuntimeError as e:
                self._invia(200, json.dumps({"ok": False, "errore": str(e)}), "application/json")
            except Exception:
                scrivi_log(traceback.format_exc())
                self._invia(200, json.dumps({"ok": False, "errore": "Errore interno: riprova."}), "application/json")
        elif self.path == "/api/mappe/cerca":
            try:
                k = carica_impostazioni().get("claude_key")
                a = str(self._corpo_json().get("auto", ""))[:80]
                if not k:
                    self._invia(200, json.dumps({"ok": False, "errore": "Prima collega Claude (chiave API) nelle Impostazioni."}), "application/json")
                elif not a:
                    self._invia(200, json.dumps({"ok": False, "errore": "Non so ancora con che auto sei: entra in pista."}), "application/json")
                else:
                    r = mappe.cerca(k, cartella_dati(), a, log=scrivi_log)
                    self._invia(200, json.dumps({"ok": True, "mappe": r}), "application/json")
            except RuntimeError as e:
                self._invia(200, json.dumps({"ok": False, "errore": str(e)}), "application/json")
            except Exception:
                scrivi_log(traceback.format_exc())
                self._invia(200, json.dumps({"ok": False, "errore": "Claude ha risposto in un formato che non capisco: riprova."}), "application/json")
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
        elif self.path == "/api/assistente/proponi":
            try:
                imp = carica_impostazioni()
                d = self._corpo_json()
                if not imp.get("claude_key") and d.get("modo") != "pressioni":
                    self._invia(200, json.dumps({"ok": False, "errore": "Prima collega Claude (chiave API)."}), "application/json")
                    return
                cartella, f = _percorso_setup(str(d.get("file", "")))
                if not f:
                    self._invia(200, json.dumps({"ok": False, "errore": "Non trovo quel setup."}), "application/json")
                    return
                percorso = os.path.join(cartella, f["auto"], f["pista"], f["nome"])
                with open(percorso, "r", encoding="utf-8-sig") as fh:
                    setup = json.load(fh)
                q = [x for x in carica_quaderno() if x.get("auto") == f["auto"] and x.get("pista") == f["pista"]][-5:]
                base = d.get("modo") == "base"
                if d.get("modo") == "pressioni":
                    sess = ultima_sessione(registro_stile().giri, f["auto"], f["pista"])
                    ris = pressioni.proposta(sess, None)
                    ris["modifiche"], ris["scartate"] = assistente.valida_modifiche(setup, ris["modifiche"], True)
                else:
                    giri_auto = [x for x in registro_stile().giri if x["auto"] == f["auto"]]
                    ris = assistente.proponi(imp["claude_key"], setup, str(d.get("sensazioni", ""))[:2000],
                                             riepilogo_gomme(), q, f["auto"], f["pista"], base=base,
                                             stile=registro_stile().profilo(f["auto"], f["pista"]), log=scrivi_log,
                                             extra=pressioni.info_per_claude(giri_auto))
                nuovo_nome = None
                if ris["modifiche"]:
                    nuovo = assistente.applica(setup, ris["modifiche"])
                    nuovo_nome = assistente.nome_nuovo_file(os.path.dirname(percorso), f["nome"])
                    tmp = os.path.join(os.path.dirname(percorso), nuovo_nome + ".tmp")
                    with open(tmp, "w", encoding="utf-8") as fh:
                        json.dump(nuovo, fh, indent=4)
                    os.replace(tmp, os.path.join(os.path.dirname(percorso), nuovo_nome))
                    voce = {"id": int(time.time()), "ora": time.strftime("%Y-%m-%d %H:%M"), "auto": f["auto"],
                            "pista": f["pista"], "da": f["nome"], "nuovo": nuovo_nome,
                            "sensazioni": str(d.get("sensazioni", ""))[:500], "problema": ris["problema"],
                            "modifiche": [{"parametro": assistente.nome_leggibile(m["percorso"]), "click": m["click"],
                                           "motivo": m["motivo"]} for m in ris["modifiche"]], "esito": None}
                    qq = carica_quaderno()
                    qq.append(voce)
                    salva_quaderno(qq[-200:])
                    ris["id"] = voce["id"]
                for m in ris["modifiche"]:
                    m["nome"] = assistente.nome_leggibile(m["percorso"])
                ris["nuovo_file"] = nuovo_nome
                ris["ok"] = True
                self._invia(200, json.dumps(ris), "application/json")
            except RuntimeError as e:
                self._invia(200, json.dumps({"ok": False, "errore": str(e)}), "application/json")
            except Exception:
                scrivi_log(traceback.format_exc())
                self._invia(200, json.dumps({"ok": False, "errore": "Errore imprevisto nell'assistente."}), "application/json")
        elif self.path == "/api/assistente/f1":
            try:
                imp = carica_impostazioni()
                d = self._corpo_json()
                if not imp.get("claude_key"):
                    self._invia(200, json.dumps({"ok": False, "errore": "Prima collega Claude (chiave API)."}), "application/json")
                    return
                st = _lettore.f1.stato()
                if not st.get("collegato") or not st.get("setup_f1"):
                    self._invia(200, json.dumps({"ok": False, "errore": "Non vedo ancora il tuo setup: apri F1 25, entra in pista (o ai box) e riprova."}), "application/json")
                    return
                base = d.get("modo") == "base"
                q = [x for x in carica_quaderno() if x.get("auto") == st["auto"] and x.get("pista") == st["pista"]][-5:]
                giri_auto = [x for x in registro_stile().giri if x["auto"] == st["auto"]]
                ris = assistente_f1.proponi(imp["claude_key"], st, str(d.get("sensazioni", ""))[:2000], riepilogo_gomme(), q,
                                            registro_stile().profilo(st["auto"], st["pista"]), base=base, log=scrivi_log,
                                            extra=None)
                if ris["modifiche"]:
                    qq = carica_quaderno()
                    n = 1 + sum(1 for x in qq if x.get("f1"))
                    voce = {"id": int(time.time()), "ora": time.strftime("%Y-%m-%d %H:%M"), "auto": st["auto"], "pista": st["pista"],
                            "da": "Setup attuale in F1", "nuovo": "Modifiche F1 n. %d" % n, "f1": True,
                            "sensazioni": str(d.get("sensazioni", ""))[:500], "problema": ris["problema"], "modifiche": ris["modifiche"],
                            "esito": None}
                    qq.append(voce)
                    salva_quaderno(qq[-200:])
                    ris["id"] = voce["id"]
                    ris["nuovo_nome"] = voce["nuovo"]
                ris["ok"] = True
                self._invia(200, json.dumps(ris), "application/json")
            except RuntimeError as e:
                self._invia(200, json.dumps({"ok": False, "errore": str(e)}), "application/json")
            except Exception:
                scrivi_log(traceback.format_exc())
                self._invia(200, json.dumps({"ok": False, "errore": "Errore imprevisto nell'assistente."}), "application/json")
        elif self.path == "/api/funzione":
            try:
                d = self._corpo_json()
                imp = carica_impostazioni()
                f = dict(imp.get("funzioni") or {})
                fid = str(d.get("id", ""))[:40]
                if fid:
                    x = dict(f.get(fid) or funzioni().get(fid) or {})
                    if "s" in d and d["s"] in ("ok", "ko", None):
                        x["s"] = d["s"]
                    if "n" in d:
                        x["n"] = str(d["n"])[:3000]
                    f[fid] = x
                    imp["funzioni"] = f
                    salva_impostazioni(imp)
                self._invia(200, json.dumps({"ok": True, "funzioni": funzioni()}), "application/json")
            except Exception:
                self._invia(200, json.dumps({"ok": False}), "application/json")
        elif self.path == "/api/assistente/esito":
            try:
                d = self._corpo_json()
                qq = carica_quaderno()
                for x in qq:
                    if x.get("id") == d.get("id") and d.get("esito") in ("meglio", "uguale", "peggio"):
                        x["esito"] = d["esito"]
                        x["esito_auto"] = False
                salva_quaderno(qq)
                self._invia(200, json.dumps({"ok": True}), "application/json")
            except Exception:
                self._invia(200, json.dumps({"ok": False, "errore": "Non sono riuscito a salvare."}), "application/json")
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
                        "stato_attuale": _lettore.stato(), "f1": getattr(getattr(_lettore, "f1", None), "diag", lambda: None)(), "setup": elenco_setup(), "setup_contenuto": contenuti_setup(), "stile": registro_stile().profilo(), "giri_registrati": len(registro_stile().giri), "funzioni": funzioni(), "mappe": mappe.leggi(cartella_dati(), _lettore.stato().get("auto") or ""), "report": crea_report(registro_stile().giri, None, registro_stile().profilo()), "sessioni": elenco_sessioni(registro_stile().giri)[:20], "log": coda_log()}
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


_aggiornando = [None]

SPLASH = """<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Simapex</title>
<body style="margin:0;background:#0e1116;color:#e8ecf2;font:22px system-ui,Arial;display:flex;align-items:center;justify-content:center;height:100vh;text-align:center">
<div><div style="font-size:42px;font-weight:700;letter-spacing:1px">SIMAPEX</div><p>Sto aggiornando alla versione __V__...</p><p style="color:#98a2b3;font-size:16px">Si riapre da solo tra pochi secondi. Non serve fare niente.</p></div>
<script>setInterval(async()=>{try{const r=await fetch("/api/stato");const j=await r.json();if(!j.aggiornando)location.reload()}catch(e){}},1500)</script>"""


def main(apri_browser=True):
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")
    srv = None
    for _ in range(12):  # se il programma vecchio sta ancora chiudendo, aspetta un attimo
        try:
            srv = ThreadingHTTPServer(("127.0.0.1", PORTA), Gestore)
            break
        except OSError:
            time.sleep(0.5)
    if srv is None:
        # già aperto: si mostra solo la pagina
        if apri_browser:
            apri_finestra("http://127.0.0.1:%d/" % PORTA)
        return
    scrivi_log("avviato versione " + VERSIONE)
    try:
        if hasattr(_lettore, "f1") and _lettore.f1.avvia():
            scrivi_log("F1 25: in ascolto sulla porta %d" % f1.PORTA)
    except Exception as e:
        scrivi_log("F1 25: avvio non riuscito (%s)" % e)
    try:
        _ptt.avvia()
        _tastiera.avvia()
    except Exception as e:
        scrivi_log("tasto radio: avvio non riuscito (%s)" % e)
    aggiorna.pulisci_vecchi()
    avviato = [False]

    def inizio(ver):
        _aggiornando[0] = ver
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        avviato[0] = True
        apri_finestra("http://127.0.0.1:%d/" % PORTA)

    def prima_di_riavviare():
        srv.shutdown()
        srv.server_close()

    if apri_browser and aggiorna.prova(VERSIONE, scrivi_log, inizio, prima_di_riavviare):
        return
    if _aggiornando[0]:  # aggiornamento non riuscito: si continua con questa versione
        _aggiornando[0] = None
        _ultima_richiesta[0] = time.time()
    if not avviato[0]:
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        if apri_browser:
            apri_finestra("http://127.0.0.1:%d/" % PORTA)
    threading.Thread(target=_guardiano, daemon=True).start()
    threading.Thread(target=_campionatore, daemon=True).start()
    _fermati.wait()
    srv.shutdown()
    scrivi_log("chiuso")
