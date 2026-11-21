# -*- coding: utf-8 -*-
"""Disegno del circuito: lo registra un giro guidato da ACC, poi resta salvato (e si può condividere)."""
import json
import math
import os
import re
import sys

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
            if gc == self.giro + 1 and not self.sporco and carica_tracciato(pista, self.cartella) is None:
                t = costruisci(self.punti)
                if t:
                    self._salva(pista, t)
            self.giro, self.punti, self.sporco, self.prec = gc, [], False, 0.0
            return
        pos, c = d.get("pos_norm"), d.get("coordinate")
        if pos is None or not c or d.get("in_box"):
            if d.get("in_box"):
                self.sporco = True
            return
        if pos < self.prec - 0.2 and self.punti:  # salto indietro: giro non pulito
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
