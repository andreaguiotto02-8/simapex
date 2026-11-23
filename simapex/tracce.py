# -*- coding: utf-8 -*-
"""Tracce dei giri (velocità, freno, gas e tempo lungo il giro): servono per il delta in diretta e per i confronti."""
import bisect
import json
import os
import time

from .circuito import nome_file

N = 200          # punti per giro
SEGMENTI = 25    # microsettori per i confronti (25 × 8 punti = 200)
TENUTI = 50      # giri tenuti per auto/pista


def _interpola(xs, ys, x):
    i = bisect.bisect_left(xs, x)
    if i <= 0:
        return ys[0]
    if i >= len(xs):
        return ys[-1]
    x0, x1 = xs[i - 1], xs[i]
    return ys[i - 1] if x1 == x0 else ys[i - 1] + (ys[i] - ys[i - 1]) * (x - x0) / (x1 - x0)


def costruisci(campioni, tempo_ms, durata_ms):
    """campioni: (posizione 0..1, ms dall'inizio giro, velocità, freno, gas). None se il giro non è utilizzabile."""
    if len(campioni) < 200 or tempo_ms <= 0:
        return None
    pos, tt = [0.0], [0.0]
    for p, t, v, f, g in campioni:
        if 0 <= p < 1 and p > pos[-1]:
            pos.append(p)
            tt.append(t)
    if len(pos) < 150:
        return None
    pos.append(1.0)
    tt.append(float(durata_ms))
    scala = tempo_ms / float(durata_ms) if durata_ms else 1.0
    t = [round(_interpola(pos, tt, k / float(N)) * scala) for k in range(N + 1)]
    if any(t[i + 1] < t[i] for i in range(N)):
        return None
    sv, sf, sg, n = [0.0] * N, [0.0] * N, [0.0] * N, [0] * N
    for p, _, v, f, g in campioni:
        if 0 <= p < 1:
            i = int(p * N)
            sv[i] += v
            sf[i] += f
            sg[i] += g
            n[i] += 1
    v, f, g = [], [], []
    for i in range(N):
        if n[i]:
            v.append(round(sv[i] / n[i])); f.append(round(sf[i] / n[i], 2)); g.append(round(sg[i] / n[i], 2))
        else:
            v.append(v[-1] if v else 0); f.append(f[-1] if f else 0); g.append(g[-1] if g else 0)
    return {"tempo_ms": int(tempo_ms), "t": t, "v": v, "f": f, "g": g}


def confronta(mio, rif):
    """Tempo perso (+) o guadagnato (-) in ms in ciascun tratto del giro rispetto al riferimento."""
    per = N // SEGMENTI
    out = []
    for s in range(SEGMENTI):
        a, b = s * per, (s + 1) * per
        out.append(round((mio["t"][b] - mio["t"][a]) - (rif["t"][b] - rif["t"][a])))
    return out


def tratti_principali(segmenti, quanti=3):
    """Indici dei tratti dove si perde di più e dove si guadagna di più."""
    ordine = sorted(range(len(segmenti)), key=lambda i: segmenti[i])
    guadagni = [i for i in ordine[:quanti] if segmenti[i] <= -20]
    perdite = [i for i in reversed(ordine[-quanti:]) if segmenti[i] >= 20]
    return guadagni, perdite


class Tracce:
    def __init__(self, cartella):
        self.cartella = cartella
        self.pista = self.auto = None
        self.giro = None
        self.camp = []
        self.t0 = None
        self.sporco = False
        self.prec = 0.0
        self._cache = {}

    def _file(self, auto, pista):
        return os.path.join(self.cartella, "%s__%s.json" % (nome_file(auto), nome_file(pista)))

    def carica(self, auto, pista):
        k = (auto, pista)
        try:
            m = os.path.getmtime(self._file(auto, pista))
        except OSError:
            return {"giri": [], "migliore": None}
        if k in self._cache and self._cache[k][0] == m:
            return self._cache[k][1]
        try:
            with open(self._file(auto, pista), "r", encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            d = {"giri": [], "migliore": None}
        self._cache[k] = (m, d)
        return d

    def _salva(self, auto, pista, giro):
        d = dict(self.carica(auto, pista))
        d["giri"] = (d.get("giri") or [])[-(TENUTI - 1):] + [giro]
        m = d.get("migliore")
        if not m or giro["tempo_ms"] < m["tempo_ms"]:
            d["migliore"] = giro
        try:
            os.makedirs(self.cartella, exist_ok=True)
            tmp = self._file(auto, pista) + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(d, f)
            os.replace(tmp, self._file(auto, pista))
        except OSError:
            pass

    def _azzera(self, d):
        self.auto, self.pista, self.giro = d.get("auto"), d.get("pista"), d.get("giri_completati")
        self.camp, self.t0, self.sporco, self.prec = [], time.time(), False, 0.0

    def trascorso_ms(self):
        return (time.time() - self.t0) * 1000.0 if self.t0 else 0.0

    def alimenta(self, d):
        if not d.get("collegato") or not d.get("pista") or d.get("giri_completati") is None:
            return
        if (d.get("auto"), d.get("pista")) != (self.auto, self.pista) or self.giro is None:
            self._azzera(d)
            return
        gc = d["giri_completati"]
        if gc != self.giro:
            if gc == self.giro + 1 and not self.sporco and d.get("ultimo_giro_ms"):
                g = costruisci(self.camp, d["ultimo_giro_ms"], self.trascorso_ms())
                if g:
                    g["ts"], g["giro"] = int(time.time()), self.giro + 1
                    self._salva(self.auto, self.pista, g)
            self._azzera(d)
            return
        pos = d.get("pos_norm")
        if d.get("in_box"):
            self.sporco = True
        if pos is None or d.get("in_box"):
            return
        if pos < self.prec - 0.2:
            self.sporco = True
        self.prec = pos
        self.camp.append((pos, self.trascorso_ms(), d.get("velocita") or 0, d.get("freno") or 0, d.get("acceleratore") or 0))

    def delta_live(self, d):
        """Differenza in ms dal tuo giro migliore nello stesso punto della pista (negativo = sei più veloce)."""
        try:
            if self.sporco or (d.get("auto"), d.get("pista")) != (self.auto, self.pista) or d.get("in_box"):
                return None
            m = self.carica(self.auto, self.pista).get("migliore")
            pos = d.get("pos_norm")
            if not m or pos is None or not (0.01 < pos < 0.99):
                return None
            return round(self.trascorso_ms() - _interpola([k / float(N) for k in range(N + 1)], m["t"], pos))
        except Exception:
            return None


def _traccia_di(tr, auto, pista, lap):
    """Trova la traccia salvata che corrisponde a un giro registrato (stesso tempo, stesso momento)."""
    for g in reversed(tr.carica(auto, pista).get("giri") or []):
        if g["tempo_ms"] == lap["tempo_ms"] and abs(g.get("ts", 0) - (lap.get("ts") or 0)) <= 20:
            return g
    return None


def _migliore_con_traccia(tr, auto, pista, laps):
    best = None
    for lap in sorted(laps, key=lambda x: x["tempo_ms"]):
        t = _traccia_di(tr, auto, pista, lap)
        if t:
            return t
    return best


def confronto_sessione(tr, auto, pista, laps_sessione, laps_precedente):
    mio = _migliore_con_traccia(tr, auto, pista, laps_sessione)
    if not mio:
        return None
    out = {"mio": {"tempo_ms": mio["tempo_ms"], "v": mio["v"], "f": mio["f"], "g": mio["g"]}, "rif": {}}
    candidati = {"precedente": _migliore_con_traccia(tr, auto, pista, laps_precedente) if laps_precedente else None,
                 "record": tr.carica(auto, pista).get("migliore")}
    for nome, r in candidati.items():
        if not r or r is mio or (r["tempo_ms"] == mio["tempo_ms"] and r.get("ts") == mio.get("ts")):
            continue
        seg = confronta(mio, r)
        guad, perd = tratti_principali(seg)
        out["rif"][nome] = {"tempo_ms": r["tempo_ms"], "v": r["v"], "segmenti": seg, "guadagni": guad, "perdite": perd,
                            "delta": [mio["t"][i] - r["t"][i] for i in range(N + 1)]}
    return out


def chiave_giro(g):
    return "%s:%s" % (int(g.get("ts", 0)), int(g["tempo_ms"]))


def lista_giri(tr, auto, pista):
    """Giri con traccia salvati per auto e pista (i più recenti prima), selezionabili per il confronto."""
    d = tr.carica(auto, pista)
    rec = d.get("migliore")
    out = []
    for g in reversed(d.get("giri") or []):
        out.append({"k": chiave_giro(g), "tempo_ms": g["tempo_ms"], "ts": g.get("ts", 0),
                    "record": bool(rec and chiave_giro(rec) == chiave_giro(g))})
    return out


def _trova(tr, auto, pista, k):
    d = tr.carica(auto, pista)
    for g in (d.get("giri") or []) + ([d["migliore"]] if d.get("migliore") else []):
        if chiave_giro(g) == k:
            return g
    return None


def confronto_giri(tr, auto, pista, ka, kb):
    """Confronto tra due giri scelti dalla lista: A (il tuo) contro B (riferimento)."""
    a, b = _trova(tr, auto, pista, ka), _trova(tr, auto, pista, kb)
    if not a or not b:
        return None
    seg = confronta(a, b)
    guad, perd = tratti_principali(seg)
    return {"mio": {"tempo_ms": a["tempo_ms"], "v": a["v"], "f": a["f"], "g": a["g"]},
            "rif": {"scelto": {"tempo_ms": b["tempo_ms"], "v": b["v"], "segmenti": seg, "guadagni": guad, "perdite": perd,
                               "delta": [a["t"][i] - b["t"][i] for i in range(N + 1)]}}}
