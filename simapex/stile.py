# -*- coding: utf-8 -*-
"""Registra in silenzio come guidi, giro per giro, e ne ricava un profilo (solo sul tuo PC)."""
import json
import math
import os
import time

NOMI_RUOTE = ["ant_sx", "ant_dx", "post_sx", "post_dx"]


def ruota_bloccata(d):
    """Indice della ruota che gira troppo piano mentre freni (blocco), oppure None."""
    w = d.get("vel_ruote")
    if not w or len(w) != 4 or (d.get("freno") or 0) < 0.3 or (d.get("velocita") or 0) < 50:
        return None
    if any((not isinstance(x, (int, float))) or math.isnan(x) or x < 0 for x in w):
        return None
    rif = max(w)
    if rif < 20:  # ruote quasi ferme: dato non valido
        return None
    i = min(range(4), key=lambda k: w[k])
    return i if w[i] < rif * 0.65 else None


class RegistroStile:
    def __init__(self, file_giri):
        self.file = file_giri
        self.giri = self._carica()
        self._azzera(None)

    def _carica(self):
        try:
            with open(self.file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _salva(self):
        try:
            tmp = self.file + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.giri[-400:], f)
            os.replace(tmp, self.file)
        except OSError:
            pass

    def _azzera(self, d):
        self.n = 0
        self.s = {"freno": 0.0, "gas": 0.0, "sterzo": 0.0, "d_sterzo": 0.0, "d_gas": 0.0}
        self.c = {"freno": 0, "gas_pieno": 0, "coasting": 0, "trail": 0}
        self.max_freno = 0.0
        self.v_min = 999.0
        self.v_max = 0.0
        self.prec = None
        self.blocchi = []
        self.gn = 0
        self.gp = [0.0] * 4
        self.gt = [0.0] * 4
        self.gz = [[0.0] * 4 for _ in range(3)]
        self.gzn = 0
        self.carb = None
        self.t_blocco = [0.0] * 4
        self.auto = d.get("auto") if d else None
        self.pista = d.get("pista") if d else None
        self.giro = d.get("giri_completati") if d else None
        self.sess = d.get("sessione") if d else None

    def alimenta(self, d):
        """Chiamato ~10 volte al secondo con lo stato letto da ACC."""
        if not d.get("collegato"):
            return
        gc = d.get("giri_completati")
        cambio = (d.get("auto"), d.get("pista")) != (self.auto, self.pista)
        if self.giro is None or cambio:
            self._azzera(d)
            return
        if gc is not None and (gc < self.giro or d.get("sessione") != self.sess):
            # nuova sessione (i giri ripartono da 0, o cambia il tipo): non perdere i giri della prossima
            self._azzera(d)
            return
        if gc is not None and gc > self.giro:
            self._chiudi(d)
            self._azzera(d)
            return
        r = ruota_bloccata(d)
        if r is not None and time.time() - self.t_blocco[r] > 1.0:
            self.blocchi.append({"ruota": NOMI_RUOTE[r], "vel": round(d.get("velocita") or 0), "freno": round(d.get("freno") or 0, 2), "pos": d.get("pos_norm")})
        if r is not None:
            self.t_blocco[r] = time.time()
        v = d.get("velocita") or 0
        self.carb = d.get("carburante", self.carb)
        self._gomme(d, v)
        if v < 20:
            return
        f, g, st = d.get("freno") or 0, d.get("acceleratore") or 0, d.get("sterzo") or 0
        self.n += 1
        self.s["freno"] += f
        self.s["gas"] += g
        self.s["sterzo"] += abs(st)
        if self.prec:
            self.s["d_sterzo"] += abs(st - self.prec[2])
            self.s["d_gas"] += abs(g - self.prec[1])
        self.prec = (f, g, st)
        self.max_freno = max(self.max_freno, f)
        self.v_min = min(self.v_min, v)
        self.v_max = max(self.v_max, v)
        if f > 0.1:
            self.c["freno"] += 1
            if abs(st) > 0.05:
                self.c["trail"] += 1
        if g > 0.95:
            self.c["gas_pieno"] += 1
        if g < 0.05 and f < 0.05:
            self.c["coasting"] += 1

    def _gomme(self, d, v):
        pr, te = d.get("pressioni") or [], d.get("temp_gomme") or []
        if v < 60 or len(pr) != 4 or len(te) != 4:
            return
        self.gn += 1
        for i in range(4):
            self.gp[i] += pr[i]
            self.gt[i] += te[i]
        z = d.get("temp_zone")
        if z and all(len(z.get(k, [])) == 4 for k in ("interna", "centro", "esterna")):
            self.gzn += 1
            for j, k in enumerate(("interna", "centro", "esterna")):
                for i in range(4):
                    self.gz[j][i] += z[k][i]

    def _gomme_giro(self):
        if self.gn < 20:
            return None
        g = {"p": [round(x / self.gn, 1) for x in self.gp], "t": [round(x / self.gn) for x in self.gt]}
        if self.gzn >= 20:
            g["z"] = [[round(x / self.gzn) for x in riga] for riga in self.gz]
        return g

    def _chiudi(self, d):
        tempo = d.get("ultimo_giro_ms") or 0
        if self.n < 200 or tempo <= 0:
            return
        n = float(self.n)
        self.giri.append({
            "auto": self.auto, "pista": self.pista, "tempo_ms": tempo, "ts": int(time.time()),
            "giro": self.giro + 1, "sess": self.sess, "pos": d.get("posizione"), "carburante": round(self.carb, 1) if self.carb is not None else None, "gomme": self._gomme_giro(), "blocchi": self.blocchi[:20],
            "freno_medio": round(self.s["freno"] / n, 3), "freno_max": round(self.max_freno, 2),
            "tempo_in_frenata": round(self.c["freno"] / n, 3),
            "frenata_con_sterzo": round(self.c["trail"] / max(1, self.c["freno"]), 3),
            "gas_pieno": round(self.c["gas_pieno"] / n, 3), "coasting": round(self.c["coasting"] / n, 3),
            "sterzo_medio": round(self.s["sterzo"] / n, 3),
            "nervosismo_sterzo": round(self.s["d_sterzo"] / n, 4), "nervosismo_gas": round(self.s["d_gas"] / n, 4),
            "vel_min": round(self.v_min), "vel_max": round(self.v_max)})
        self._salva()

    def profilo(self, auto=None, pista=None, ultimi=30):
        """Medie sui giri puliti (tempo entro il 107% del migliore) di quell'auto."""
        g = [x for x in self.giri if (auto is None or x["auto"] == auto)]
        if pista:
            g = [x for x in g if x["pista"] == pista] or g
        if not g:
            return None
        migliore = min(x["tempo_ms"] for x in g)
        puliti = [x for x in g if x["tempo_ms"] <= migliore * 1.07][-ultimi:]
        if len(puliti) < 3:
            return None
        chiavi = ["freno_medio", "freno_max", "tempo_in_frenata", "frenata_con_sterzo", "gas_pieno", "coasting",
                  "sterzo_medio", "nervosismo_sterzo", "nervosismo_gas"]
        out = {k: round(sum(x[k] for x in puliti) / len(puliti), 3) for k in chiavi}
        out["giri_considerati"] = len(puliti)
        out["costanza_tempi_ms"] = round(max(x["tempo_ms"] for x in puliti) - min(x["tempo_ms"] for x in puliti))
        return out
