# -*- coding: utf-8 -*-
"""F1 25 (anche con il pacchetto 2026): lettura della telemetria UDP e traduzione nello stesso formato dei dati di ACC.

Il gioco manda i dati a 127.0.0.1 sulla porta 20777 (Impostazioni -> Telemetria -> UDP, formato 2025).
Si usa solo la libreria standard. Ogni pacchetto viene controllato sulla lunghezza: se una lunghezza non è quella attesa
si salta il pacchetto e si annota in `diag()`, così un cambio di formato non rompe il programma."""
import socket
import struct
import threading
import time

PORTA = 20777
GIRI_NUM = 22  # auto nei pacchetti di F1 25
INTESTAZIONE = 29
RAGGIO_RUOTA_M = 0.33  # per passare dai m/s delle ruote ai rad/s che usa il rilevatore dei blocchi

# id pacchetto
MOTO, SESSIONE, GIRI, EVENTO, PARTECIPANTI, SETUP, TELEMETRIA, STATO_AUTO, FINALE, LOBBY, DANNI, STORICO, GOMME, MOTO_EX = range(14)

# lunghezze attese (F1 25, 22 auto): {id: (dimensione auto, byte finali)}
DIM_AUTO = {MOTO: (60, 0), GIRI: (57, 2), TELEMETRIA: (60, 3), STATO_AUTO: (55, 0), DANNI: (46, 0), SETUP: (50, 4)}
LUNG_SESSIONE_MIN = 40
LUNG_MOTO_EX = 273

SQUADRE = {0: "mercedes", 1: "ferrari", 2: "red_bull", 3: "williams", 4: "aston_martin", 5: "alpine", 6: "racing_bulls",
           7: "haas", 8: "mclaren", 9: "sauber", 41: "generica", 104: "personalizzata"}
PISTE = {0: "melbourne", 2: "shanghai", 3: "sakhir", 4: "catalunya", 5: "monaco", 6: "montreal", 7: "silverstone", 9: "hungaroring",
         10: "spa", 11: "monza", 12: "singapore", 13: "suzuka", 14: "abu_dhabi", 15: "austin", 16: "interlagos", 17: "austria",
         19: "mexico", 20: "baku", 26: "zandvoort", 27: "imola", 29: "jeddah", 30: "miami", 31: "las_vegas", 32: "losail",
         39: "silverstone_inversa", 40: "austria_inversa", 41: "zandvoort_inversa"}


MESCOLE = {16: "morbida", 17: "media", 18: "dura", 7: "intermedia", 8: "bagnato", 19: "morbida", 20: "media", 21: "dura"}
BANDIERE = {1: "verde", 2: "blu", 3: "gialla", 4: "rossa"}
METEO = {0: "sereno", 1: "poco nuvoloso", 2: "coperto", 3: "pioggia leggera", 4: "pioggia forte", 5: "temporale"}
SAFETY = {1: "safety car", 2: "safety car virtuale", 3: "giro di formazione"}


def tipo_sessione(t):
    """Stessi codici di ACC: 0 prove, 1 qualifica, 2 gara, 3 giro lanciato (cronometro)."""
    if t in (1, 2, 3, 4):
        return 0
    if 5 <= t <= 14:
        return 1
    if t in (15, 16, 17):
        return 2
    if t == 18:
        return 3
    return -1


# F1 numera le ruote RL, RR, FL, FR; ACC FL, FR, RL, RR
def _ruote(v):
    return [v[2], v[3], v[0], v[1]]


def _marcia(g):
    return "R" if g < 0 else "N" if g == 0 else str(g)


def chi_usa_porta(porta):
    """Nome del programma che tiene la porta UDP (solo Windows; None se non si riesce a capire)."""
    import subprocess
    import sys
    if not sys.platform.startswith("win"):
        return None
    try:
        fl = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        out = subprocess.run(["netstat", "-ano", "-p", "UDP"], capture_output=True, text=True, timeout=8, creationflags=fl).stdout
        pids = []
        for riga in out.splitlines():
            p = riga.split()
            if len(p) >= 4 and p[0].upper() == "UDP" and p[1].endswith(":%d" % porta) and p[-1].isdigit():
                pids.append(p[-1])
        nomi = []
        for pid in dict.fromkeys(pids):
            t = subprocess.run(["tasklist", "/FI", "PID eq " + pid, "/FO", "CSV", "/NH"], capture_output=True, text=True, timeout=8, creationflags=fl).stdout.strip()
            if t.startswith('"'):
                n = t.split('","')[0].strip('"')
                if n and n.lower() != "simapex.exe" and n not in nomi:
                    nomi.append(n)
        return ", ".join(nomi) or None
    except Exception:
        return None


class LettoreF1:
    def __init__(self, porta=PORTA, log=None):
        self.porta = porta
        self.log = log or (lambda m: None)
        self.d = {}
        self.ultimo = 0.0
        self.diag_pacchetti = {}   # {id: [conteggio, ultima lunghezza]}
        self.scartati = {}         # {id: lunghezza} pacchetti con lunghezza inattesa
        self.formato = None
        self.player = 0
        self.migliore_ms = None
        self._giro_prec = None
        self._invalido = False
        self._sock = None
        self._ferma = False
        self.errore = None
        self.occupata_da = None
        self.squadra = None
        self.pista_nome = None

    # ---- ciclo di vita ----
    def avvia(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("0.0.0.0", self.porta))
            s.settimeout(1.0)
            self._sock = s
        except OSError as e:
            self.errore = "porta %d occupata o bloccata (%s)" % (self.porta, e)
            ora = time.time()
            if ora - getattr(self, "_ultimo_log", 0) > 900 or not getattr(self, "_ultimo_log", 0):
                # il controllo di chi occupa la porta e la riga nel registro si fanno rari: niente scatti e registro leggibile
                self._ultimo_log = ora
                self.occupata_da = chi_usa_porta(self.porta) or self.occupata_da
                self.log("F1: " + self.errore + (" - usata da " + self.occupata_da if self.occupata_da else ""))
            return False
        self.errore = None
        self.occupata_da = None
        threading.Thread(target=self._ciclo, daemon=True).start()
        return True

    def riprova(self):
        """Se la porta era occupata, ritenta: appena l'altro programma si chiude F1 si collega da solo."""
        if self._sock is None and not self._ferma:
            vecchio = self.occupata_da
            if self.avvia():
                self.log("F1 25: porta liberata, in ascolto")
                return True
            if vecchio and not self.occupata_da:
                self.occupata_da = vecchio
        return False

    def problema(self):
        """Frase semplice da mostrare a Otto se F1 non può ricevere i dati."""
        if self._sock is not None or not self.errore:
            return None
        chi = self.occupata_da
        if chi:
            return "F1 25 non riesce a mandare i dati a Simapex perché un altro programma sta usando la stessa porta: %s. Chiudilo (o spegni il suo ascolto di F1) e Simapex si collega da solo." % chi
        return "F1 25 non riesce a mandare i dati a Simapex: la porta è occupata da un altro programma (per esempio Track Titan). Chiudi gli altri programmi di telemetria e Simapex si collega da solo."

    def ferma(self):
        self._ferma = True
        try:
            if self._sock:
                self._sock.close()
        except OSError:
            pass

    def _ciclo(self):
        while not self._ferma:
            try:
                b, _ = self._sock.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError:
                return
            try:
                self.elabora(b)
            except Exception as e:  # un pacchetto strano non deve fermare il programma
                self.errore = "%s: %s" % (type(e).__name__, e)

    # ---- interpretazione ----
    def elabora(self, b):
        if len(b) < INTESTAZIONE:
            return
        formato, anno, _maj, _min, _ver, pid = struct.unpack_from("<HBBBBB", b, 0)
        self.player = b[27]
        self.formato = (formato, anno)
        self.ultimo = time.time()
        c = self.diag_pacchetti.setdefault(pid, [0, 0])
        c[0] += 1
        c[1] = len(b)
        i = self.player
        if pid in DIM_AUTO:
            dim, fine = DIM_AUTO[pid]
            n = (len(b) - INTESTAZIONE - fine) / float(dim)
            if n != int(n) or int(n) < 20 or i >= int(n):
                self.scartati[pid] = len(b)
                return
            o = INTESTAZIONE + i * dim
            if pid == TELEMETRIA:
                self._telemetria(b, o)
            elif pid == GIRI:
                self._giri(b, o)
                self._distacchi(b, int(n), dim)
            elif pid == STATO_AUTO:
                self._stato_auto(b, o)
            elif pid == SETUP:
                self._setup(b, o)
            elif pid == DANNI:
                u = struct.unpack_from("<4f", b, o)
                self.d["usura_gomme"] = [round(x, 1) for x in _ruote(u)]
            elif pid == MOTO:
                x, y, z = struct.unpack_from("<fff", b, o)
                self.d["coordinate"] = [round(x, 1), round(y, 1), round(z, 1)]
        elif pid == SESSIONE and len(b) >= LUNG_SESSIONE_MIN:
            self._sessione(b)
        elif pid == PARTECIPANTI and len(b) >= INTESTAZIONE + 1 + (i + 1) * 57:
            team = b[INTESTAZIONE + 1 + i * 57 + 3]
            self.squadra = SQUADRE.get(team, "team_%d" % team)
        elif pid == MOTO_EX and len(b) >= 77 + 16:
            w = struct.unpack_from("<4f", b, 77)
            self.d["vel_ruote"] = [round(x / RAGGIO_RUOTA_M, 2) for x in _ruote(w)]

    def _telemetria(self, b, o):
        vel, acc, ster, fre = struct.unpack_from("<Hfff", b, o)
        gear, rpm = struct.unpack_from("<bH", b, o + 15)
        freni = struct.unpack_from("<4H", b, o + 22)
        interna = struct.unpack_from("<4B", b, o + 34)
        press = struct.unpack_from("<4f", b, o + 40)
        self.d.update({"velocita": float(vel), "acceleratore": round(acc, 3), "sterzo": round(ster, 3), "freno": round(fre, 3),
                       "marcia": _marcia(gear), "giri_motore": rpm, "temp_freni": [float(x) for x in _ruote(freni)],
                       "temp_gomme": [float(x) for x in _ruote(interna)], "pressioni": [round(x, 2) for x in _ruote(press)]})

    def _giri(self, b, o):
        ultimo, corrente = struct.unpack_from("<II", b, o)
        dist, = struct.unpack_from("<f", b, o + 20)
        pos, giro, pit, _np, _sett, invalido = struct.unpack_from("<6B", b, o + 32)
        lunghezza = self.d.get("_lunghezza_pista") or 0
        if giro != self._giro_prec:
            if self._giro_prec is not None and giro == self._giro_prec + 1 and 0 < ultimo < 36000000 and not self._invalido:
                if self.migliore_ms is None or ultimo < self.migliore_ms:
                    self.migliore_ms = ultimo
            self._giro_prec = giro
            self._invalido = False
        if invalido:
            self._invalido = True
        self.d.update({"giri_completati": max(0, giro - 1), "giro_corrente_ms": corrente,
                       "ultimo_giro_ms": ultimo if ultimo > 0 else 2147483647,
                       "miglior_giro_ms": self.migliore_ms if self.migliore_ms else 2147483647,
                       "posizione": pos, "in_box": pit > 0, "giro_valido": not self._invalido,
                       "pos_norm": round(max(0.0, min(0.9999, dist / lunghezza)), 5) if lunghezza > 0 else 0.0})

    def _setup(self, b, o):
        ala_a, ala_p, diff_in, diff_out = struct.unpack_from("<4B", b, o)
        camb_a, camb_p, conv_a, conv_p = struct.unpack_from("<4f", b, o + 4)
        sosp_a, sosp_p, barra_a, barra_p, alt_a, alt_p, press_fr, bias, freno_mot = struct.unpack_from("<9B", b, o + 20)
        rl, rr, fl, fr = struct.unpack_from("<4f", b, o + 29)
        zav, = struct.unpack_from("<B", b, o + 45)
        carb, = struct.unpack_from("<f", b, o + 46)
        self.d["setup_f1"] = {"ala anteriore": ala_a, "ala posteriore": ala_p, "differenziale in accelerazione %": diff_in,
                              "differenziale in rilascio %": diff_out, "campanatura anteriore": round(camb_a, 2),
                              "campanatura posteriore": round(camb_p, 2), "convergenza anteriore": round(conv_a, 2),
                              "convergenza posteriore": round(conv_p, 2), "sospensioni anteriori": sosp_a,
                              "sospensioni posteriori": sosp_p, "barra anteriore": barra_a, "barra posteriore": barra_p,
                              "altezza anteriore": alt_a, "altezza posteriore": alt_p, "pressione freni %": press_fr,
                              "ripartizione freni % anteriore": bias, "freno motore %": freno_mot,
                              "pressioni gomme psi (AS, AD, PS, PD)": [round(x, 1) for x in (fl, fr, rl, rr)],
                              "zavorra": zav, "carburante a inizio sessione": round(carb, 1)}

    def _distacchi(self, b, n, dim):
        """Distacco dalla macchina davanti e vantaggio su quella dietro, e tempi dell'ultimo giro dei due."""
        auto = []
        for k in range(n):
            q = INTESTAZIONE + k * dim
            ultimo, = struct.unpack_from("<I", b, q)
            ms, mn = struct.unpack_from("<HB", b, q + 14)
            lms, lmn = struct.unpack_from("<HB", b, q + 17)
            pos = b[q + 32]
            auto.append((pos, ultimo, ms + mn * 60000, lms + lmn * 60000))
        mio = auto[self.player]
        if mio[0] <= 0:
            return

        def vicino(p):
            for a in auto:
                if a[0] == p:
                    return a
            return None
        dav, dietro = vicino(mio[0] - 1), vicino(mio[0] + 1)
        self.d["gap_leader_ms"] = mio[3]
        self.d["gap_altri_ms"] = sorted(a[3] for k, a in enumerate(auto) if k != self.player and a[0] > 0)
        for k in ("distacco_davanti_ms", "distacco_dietro_ms", "ultimo_davanti_ms", "ultimo_dietro_ms"):
            self.d.pop(k, None)
        if dav and mio[2] > 0:
            self.d["distacco_davanti_ms"] = mio[2]
            if dav[1] > 0:
                self.d["ultimo_davanti_ms"] = dav[1]
        if dietro and dietro[2] > 0:
            self.d["distacco_dietro_ms"] = dietro[2]
            if dietro[1] > 0:
                self.d["ultimo_dietro_ms"] = dietro[1]

    def _stato_auto(self, b, o):
        tc, abs_, _mix, bias, limitatore = struct.unpack_from("<5B", b, o)
        carb, = struct.unpack_from("<f", b, o + 5)
        self.d.update({"carburante": round(carb, 2), "abs": float(abs_), "controllo_trazione": tc, "bilanciamento_freni": bias,
                       "limitatore": limitatore})
        if o + 42 <= len(b):
            giri_c, = struct.unpack_from("<f", b, o + 13)
            mesc, eta, bandiera = b[o + 26], b[o + 27], struct.unpack_from("<b", b, o + 28)[0]
            ers, = struct.unpack_from("<f", b, o + 37)
            self.d.update({"giri_carburante_gioco": round(giri_c, 1), "mescola": MESCOLE.get(mesc, ""), "eta_gomme": eta,
                           "bandiera": BANDIERE.get(bandiera, ""), "ers_pct": round(max(0.0, min(100.0, ers / 4000000.0 * 100)))})

    def _sessione(self, b):
        meteo, t_pista, t_aria, giri_tot = struct.unpack_from("<BbbB", b, INTESTAZIONE)
        lung, tipo, pista = struct.unpack_from("<HBb", b, INTESTAZIONE + 4)
        self.d["_lunghezza_pista"] = lung
        self.d["meteo"] = METEO.get(meteo, "")
        self.d["temp_aria"] = float(t_aria)
        self.d["temp_asfalto"] = float(t_pista)
        self.d["sessione"] = tipo_sessione(tipo)
        if giri_tot:
            self.d["giri_totali"] = giri_tot
        if len(b) >= INTESTAZIONE + 11:
            rim, = struct.unpack_from("<H", b, INTESTAZIONE + 9)
            self.d["tempo_rimasto_s"] = rim
        if len(b) >= INTESTAZIONE + 125:
            self.d["safety_car"] = SAFETY.get(b[INTESTAZIONE + 124], "")
        self.pista_nome = PISTE.get(pista, "circuito_%d" % pista)

    # ---- uscita ----
    def stato(self):
        if time.time() - self.ultimo > 3.0 or not self.d:
            return {"collegato": False}
        d = {k: v for k, v in self.d.items() if not k.startswith("_")}
        d.update({"collegato": True, "gioco": "F1 25", "stato_codice": 2, "stato_gioco": "in pista",
                  "auto": "f1_" + (self.squadra or "auto"), "pista": self.pista_nome or "circuito",
                  "ultimo_giro": "", "miglior_giro": ""})
        from .telemetria import formatta_tempo
        d["ultimo_giro"] = formatta_tempo(d.get("ultimo_giro_ms"))
        d["miglior_giro"] = formatta_tempo(d.get("miglior_giro_ms"))
        return d

    def diag(self):
        return {"formato": self.formato, "pacchetti": self.diag_pacchetti, "scartati": self.scartati, "errore": self.errore,
                "porta": self.porta, "giocatore": self.player, "occupata_da": self.occupata_da}


class LettoreMulti:
    """ACC (memoria condivisa) se è aperto, altrimenti F1 25 (UDP)."""

    def __init__(self, acc, f1):
        self.acc, self.f1 = acc, f1

    def stato(self):
        s = self.acc.stato()
        # ACC conta come aperto solo se i suoi dati si muovono davvero: la memoria condivisa può
        # restare presente (ACC chiuso male, altri programmi) anche col gioco chiuso
        ora = time.time()
        pid = s.get("pacchetto")
        if pid is not None and pid != getattr(self, "_pid", None):
            self._pid, self._t_pid = pid, ora
        movimento = pid is None or ora - getattr(self, "_t_pid", 0) < 3
        acc_vivo = bool(s.get("collegato")) and s.get("stato_codice") not in (0, None) and movimento
        if acc_vivo:
            s["gioco"] = "ACC"
            return s
        f = self.f1.stato()
        if f.get("collegato"):
            return f
        s["collegato"] = False
        return s
        f = self.f1.stato()
        if f.get("collegato"):
            return f
        if s.get("collegato"):
            s["gioco"] = "ACC"
        return s
