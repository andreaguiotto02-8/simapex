# -*- coding: utf-8 -*-
"""Community e calendario: eventi ACC pubblici da SimGrid (letti dal PC di Otto) con etichette, e calendario delle sue sessioni."""
import datetime
import html as _html
import json
import os
import re
import time
import urllib.request

URL_CALENDARIO = "https://www.thesimgrid.com/calendar"
ITALIANE = ("ROMAGNOLI", "FMP", "ROVENTE", "FOX", "IRC", "ITALIAN", "RACEHUB", "RHM", "PWRACING", "ALPHA CORSA")
_BLOCCO = re.compile(r'<div[^>]*class="[^"]*rounded-2[^"]*mb-2[^"]*"[^>]*>(.*?)(?=<div[^>]*class="[^"]*rounded-2[^"]*mb-2|\Z)', re.S)
_TIME = re.compile(r'<time[^>]*datetime="([^"]+)"', re.S)
_LINK = re.compile(r'<a[^>]*href="(/championships/\d+)"[^>]*>(.*?)</a>', re.S)


def _testo(h):
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


def _ora_italiana(dt_utc):
    """UTC -> ora italiana (CET inverno, CEST dal ultima dom di marzo a ultima dom di ottobre)."""
    def ultima_dom(y, m):
        d = datetime.datetime(y, m, 31 if m in (3, 10) else 30)
        while d.weekday() != 6:
            d -= datetime.timedelta(days=1)
        return d.replace(hour=1)
    y = dt_utc.year
    legale = ultima_dom(y, 3) <= dt_utc < ultima_dom(y, 10)
    return dt_utc + datetime.timedelta(hours=2 if legale else 1)


def parse(html_testo):
    """Eventi ACC dal calendario SimGrid: [{inizio_utc, quando, nome, link, piattaforma, organizzatore, testo}]."""
    out = []
    for b in _BLOCCO.findall(html_testo or ""):
        t, l = _TIME.search(b), _LINK.search(b)
        if not t or not l:
            continue
        txt = _testo(b)
        if "ACC" not in txt.upper().split("ASSETTO")[0] and "Assetto Corsa Competizione" not in txt:
            if not re.search(r"\bACC\b", txt):
                continue
        try:
            dt = datetime.datetime.strptime(t.group(1)[:19].replace(" ", "T"), "%Y-%m-%dT%H:%M:%S")
        except Exception:
            continue
        nome = _testo(l.group(2))
        m = re.search(r"\bACC\s*-\s*(PC|CROSSPLAY|PLAYSTATION|XBOX)\s*(.*)$", txt)
        out.append({"inizio_utc": dt.isoformat(), "quando": _ora_italiana(dt).strftime("%Y-%m-%d %H:%M"), "nome": nome,
                    "link": "https://www.thesimgrid.com" + l.group(1), "piattaforma": m.group(1) if m else "",
                    "organizzatore": (m.group(2).strip() if m else ""), "italiana": False})
    for e in out:
        s = (e["nome"] + " " + e["organizzatore"]).upper()
        e["italiana"] = any(k in s for k in ITALIANE)
    return out


def durata_min(nome):
    n = (nome or "").lower()
    m = re.search(r"(\d+)\s*(?:h|ore|hours?)\b", n)
    if m:
        return int(m.group(1)) * 60
    m = re.search(r"(\d+)\s*(?:min|minuti|minutes|')", n)
    return int(m.group(1)) if m else None


def etichetta(ev):
    """«fattibile» / «tosta» / «fuori orario» in base a orario (gioca la sera o nel weekend) e durata."""
    try:
        d = datetime.datetime.strptime(ev["quando"], "%Y-%m-%d %H:%M")
    except Exception:
        return "fuori orario"
    weekend = d.weekday() >= 5
    ora = d.hour + d.minute / 60.0
    if not (weekend and 14 <= ora <= 23.5) and not (18.5 <= ora <= 23.0):
        return "fuori orario"
    dur = durata_min(ev.get("nome"))
    if dur and dur > 120:
        return "tosta"
    if ev.get("piattaforma") in ("PLAYSTATION", "XBOX"):
        return "tosta"
    return "fattibile"


def filtra(eventi, adesso=None, giorni=14, solo_gt=True):
    adesso = adesso or datetime.datetime.utcnow()
    lim = adesso + datetime.timedelta(days=giorni)
    out = []
    for e in eventi:
        try:
            d = datetime.datetime.strptime(e["inizio_utc"][:19], "%Y-%m-%dT%H:%M:%S")
        except Exception:
            continue
        if not (adesso <= d <= lim):
            continue
        if e.get("piattaforma") not in ("PC", "CROSSPLAY"):
            continue
        n = e["nome"].upper()
        if solo_gt and "GT3" not in n and "GT4" not in n and "GT" not in n and not e.get("italiana"):
            continue
        x = dict(e)
        x["etichetta"] = etichetta(e)
        out.append(x)
    out.sort(key=lambda x: (not x["italiana"], x["etichetta"] != "fattibile", x["inizio_utc"]))
    return out[:40]


def _f(cartella, nome):
    return os.path.join(cartella, nome)


def eventi(cartella, forza=False):
    """Scarica il calendario (cache 3 ore). Se la rete non va usa l'ultima copia."""
    p = _f(cartella, "community_eventi.json")
    cache = {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            cache = json.load(f)
    except Exception:
        pass
    if not forza and cache.get("t") and time.time() - cache["t"] < 3 * 3600:
        return cache.get("eventi", []), True
    try:
        req = urllib.request.Request(URL_CALENDARIO, headers={"User-Agent": "Mozilla/5.0 Simapex"})
        with urllib.request.urlopen(req, timeout=20) as r:
            ev = parse(r.read(8000000).decode("utf-8", "replace"))
        if ev:
            os.makedirs(cartella, exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                json.dump({"t": time.time(), "eventi": ev}, f, ensure_ascii=False)
            return ev, True
    except Exception:
        pass
    return cache.get("eventi", []), False


# ---- calendario personale ----
def carica(cartella):
    try:
        with open(_f(cartella, "calendario.json"), "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, list) else []
    except Exception:
        return []


def _salva(cartella, voci):
    os.makedirs(cartella, exist_ok=True)
    with open(_f(cartella, "calendario.json"), "w", encoding="utf-8") as f:
        json.dump(voci, f, ensure_ascii=False, indent=1)


def aggiungi(cartella, quando, titolo, tipo="sessione", online=False, nota=""):
    voci = carica(cartella)
    nuovo = max([x.get("id", 0) for x in voci] + [int(time.time() * 1000) - 1]) + 1
    v = {"id": nuovo, "quando": str(quando)[:16], "titolo": str(titolo)[:120], "tipo": tipo,
         "online": bool(online), "nota": str(nota)[:200], "fatto": False}
    voci.append(v)
    voci.sort(key=lambda x: x["quando"])
    _salva(cartella, voci)
    return v


def togli(cartella, id_):
    _salva(cartella, [v for v in carica(cartella) if v.get("id") != id_])


def segna_fatto(cartella, id_):
    voci = carica(cartella)
    for v in voci:
        if v.get("id") == id_:
            v["fatto"] = True
    _salva(cartella, voci)


def proponi_prossima(cartella, auto, pista, obiettivo_testo, adesso=None):
    """Dopo una sessione: propone la prossima (domani sera 21:00, o 3 giorni dopo se domani è già pieno) con l'obiettivo."""
    adesso = adesso or datetime.datetime.now()
    occupati = {v["quando"][:10] for v in carica(cartella) if not v.get("fatto")}
    d = (adesso + datetime.timedelta(days=1)).replace(hour=21, minute=0, second=0, microsecond=0)
    while d.strftime("%Y-%m-%d") in occupati:
        d += datetime.timedelta(days=1)
    t = "%s - %s" % (pista or "pista", auto or "auto")
    return aggiungi(cartella, d.strftime("%Y-%m-%d %H:%M"), t, "proposta", False, obiettivo_testo or "")
