# -*- coding: utf-8 -*-
"""Disegno del circuito: lo registra un giro guidato da ACC, poi resta salvato (e si può condividere)."""
import json
import math
import os
import re
import sys
import time

PUNTI = 400  # punti per giro


def nome_file(pista):
    return re.sub(r"[^a-z0-9_]+", "_", str(pista or "").lower()).strip("_") or "pista"


def cartella_inclusa():
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, "simapex", "piste")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "piste")


def carica_tracciato(pista, cartella_utente):
    for base in (cartella_utente, cartella_inclusa()):
        try:
            with open(os.path.join(base, nome_file(pista) + ".json"), "r", encoding="utf-8") as f:
                t = json.load(f)
            if t.get("x") and len(t["x"]) == len(t["z"]):
                return t
        except Exception:
            continue
    return None


def costruisci(punti):
    """punti: lista (posizione 0..1, x, z, velocità). Restituisce il disegno ricampionato o None se non plausibile."""
    if len(punti) < 300:
        return None
    sx = [0.0] * PUNTI
    sz = [0.0] * PUNTI
    sv = [0.0] * PUNTI
    n = [0] * PUNTI
    for p, x, z, v in punti:
        if not (0 <= p < 1) or any(math.isnan(a) or math.isinf(a) for a in (x, z, v)):
            continue
        i = int(p * PUNTI)
        sx[i] += x
        sz[i] += z
        sv[i] += v
        n[i] += 1
    if sum(1 for k in n if k) < PUNTI * 0.9:
        return None
    # riempie i buchi con il punto precedente
    xs, zs, vs = [], [], []
    for i in range(PUNTI):
        if n[i]:
            xs.append(sx[i] / n[i]); zs.append(sz[i] / n[i]); vs.append(sv[i] / n[i])
        else:
            xs.append(xs[-1] if xs else 0.0); zs.append(zs[-1] if zs else 0.0); vs.append(vs[-1] if vs else 0.0)
    passi = [math.hypot(xs[i] - xs[i - 1], zs[i] - zs[i - 1]) for i in range(1, PUNTI)]
    ampiezza = max(max(xs) - min(xs), max(zs) - min(zs))
    if ampiezza < 150 or max(passi) > 150:  # troppo piccolo o con salti: dato non valido
        return None
    lunghezza = sum(passi)
    return {"x": [round(a, 1) for a in xs], "z": [round(a, 1) for a in zs], "v": [round(a) for a in vs],
            "lunghezza_m": round(lunghezza), "origine": "registrato da ACC"}


class Registratore:
    """Registra la posizione durante ogni giro; al primo giro valido per una pista salva il disegno."""

    def __init__(self, cartella, alla_creazione=None):
        self.cartella = cartella
        self.alla_creazione = alla_creazione
        self.punti = []
        self.giro = None
        self.pista = None
        self.sporco = False
        self.prec = 0.0
        self.controllo_validita = False

    def alimenta(self, d):
        if not d.get("collegato"):
            return
        pista, gc = d.get("pista"), d.get("giri_completati")
        if not pista or gc is None:
            return
        if pista != self.pista or self.giro is None:
            self.pista, self.giro, self.punti, self.sporco, self.prec = pista, gc, [], False, 0.0
            return
        if gc != self.giro:
            if gc == self.giro + 1 and not self.sporco:
                vecchio = carica_tracciato(pista, self.cartella)
                # si disegna col primo giro pulito; un disegno fatto prima senza controllo della validità si rifà al primo giro valido
                if vecchio is None or (self.controllo_validita and not vecchio.get("pulito") and vecchio.get("origine") == "registrato da ACC"):
                    t = costruisci(self.punti)
                    if t:
                        t["pulito"] = bool(self.controllo_validita)
                        self._salva(pista, t)
            self.giro, self.punti, self.sporco, self.prec = gc, [], False, 0.0
            return
        pos, c = d.get("pos_norm"), d.get("coordinate")
        if d.get("giro_valido") is True:
            self.controllo_validita = True    # il dato esiste ed è credibile (l'ho visto "valido" almeno una volta)
        if self.controllo_validita and d.get("giro_valido") is False:
            self.sporco = True               # fuori pista o limiti tagliati: questo giro non serve per il disegno
        if pos is None or not c or d.get("in_box"):
            if d.get("in_box"):
                self.sporco = True
            return
        if pos < self.prec - 0.2 and self.prec < 0.9 and self.punti:  # salto indietro a metà giro: giro non pulito (a fine giro è normale)
            self.sporco = True
        self.prec = pos
        self.punti.append((pos, c[0], c[2], d.get("velocita") or 0))

    def _salva(self, pista, t):
        try:
            os.makedirs(self.cartella, exist_ok=True)
            t["pista"] = pista
            percorso = os.path.join(self.cartella, nome_file(pista) + ".json")
            with open(percorso + ".tmp", "w", encoding="utf-8") as f:
                json.dump(t, f)
            os.replace(percorso + ".tmp", percorso)
            if self.alla_creazione:
                self.alla_creazione(pista, t)
        except OSError:
            pass


def _file_box(cartella, pista):
    return os.path.join(cartella, nome_file(pista) + "__box.json")


def carica_box(cartella, pista):
    try:
        with open(_file_box(cartella, pista), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _mediana(v):
    v = sorted(v)
    return v[len(v) // 2] if v else None


class Box:
    """Corsia dei box: ne registra il disegno, quanto ci metti a percorrerla e quanto stai fermo."""

    def __init__(self, cartella):
        self.cartella = cartella
        self.pista = None
        self.dentro = False
        self.t_in = self.t_prec = 0.0
        self.pts = []
        self.fermo = 0.0
        self.pos_in = self.prec_pos = None
        self.auto = None

    def alimenta(self, d, ora=None):
        if not d.get("collegato") or not d.get("pista"):
            return
        now = ora if ora is not None else time.time()
        if d["pista"] != self.pista:
            self.pista, self.dentro, self.pts = d["pista"], False, []
        ib = bool(d.get("in_box"))
        pos = d.get("pos_norm")
        if ib and not self.dentro:
            self.dentro, self.t_in, self.t_prec, self.pts, self.fermo = True, now, now, [], 0.0
            self.pos_in, self.auto = self.prec_pos, d.get("auto")
        elif ib:
            c = d.get("coordinate")
            if c:
                self.pts.append((c[0], c[2]))
            if (d.get("velocita") or 0) < 3:
                self.fermo += now - self.t_prec
            self.t_prec = now
        elif self.dentro:
            self.dentro = False
            dur = now - self.t_in
            if 8 <= dur <= 300 and len(self.pts) >= 20:
                self._salva(dur, pos)
        self.prec_pos = pos

    def _salva(self, dur, pos_out):
        try:
            b = carica_box(self.cartella, self.pista) or {}
            if not b.get("x"):
                passo = max(1, len(self.pts) // 120)
                pts = self.pts[::passo]
                b["x"], b["z"] = [round(x, 1) for x, _ in pts], [round(z, 1) for _, z in pts]
                b["entra"], b["esce"] = self.pos_in, pos_out
            fermo = self.fermo if self.fermo >= 1.5 else 0.0
            b["soste"] = (b.get("soste") or [])[-29:] + [{"ts": int(time.time()), "auto": self.auto, "corsia_ms": round(dur * 1000),
                                                          "fermo_ms": round(fermo * 1000)}]
            os.makedirs(self.cartella, exist_ok=True)
            with open(_file_box(self.cartella, self.pista) + ".tmp", "w", encoding="utf-8") as f:
                json.dump(b, f)
            os.replace(_file_box(self.cartella, self.pista) + ".tmp", _file_box(self.cartella, self.pista))
        except OSError:
            pass


def info_box(cartella, pista, auto, miglior_traccia, N=200):
    """Tempo perso in corsia box: transito (senza sosta) meno il tempo che ci metteresti in pista per lo stesso tratto."""
    b = carica_box(cartella, pista)
    if not b or not b.get("soste") or b.get("entra") is None or b.get("esce") is None or not miglior_traccia:
        return None
    s = [x for x in b["soste"] if x.get("auto") == auto] or []
    if not s:
        return None
    transito = _mediana([x["corsia_ms"] - x["fermo_ms"] for x in s])
    soste = [x["fermo_ms"] for x in s if x["fermo_ms"] > 0]
    t = miglior_traccia["t"]

    def at(p):
        i = max(0.0, min(0.9999, p)) * N
        k = int(i)
        return t[k] + (t[k + 1] - t[k]) * (i - k)
    a, e = b["entra"], b["esce"]
    in_pista = (at(e) - at(a)) if e >= a else (t[N] - at(a) + at(e))
    out = {"transito_ms": round(transito), "tempo_pista_ms": round(in_pista), "perdita_ms": round(transito - in_pista),
           "fermo_ms": round(_mediana(soste)) if soste else None, "soste": len(soste)}
    out["perdita_con_sosta_ms"] = out["perdita_ms"] + (out["fermo_ms"] or 0)
    return out
