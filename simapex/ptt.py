# -*- coding: utf-8 -*-
"""Tasto «parla» sul volante: legge i pulsanti dei controller di Windows (stessi numeri di joy.cpl, partendo da 1)."""
import sys
import threading
import time


def _lettore_windows():
    import ctypes

    class JOYINFOEX(ctypes.Structure):
        _fields_ = [(n, ctypes.c_uint32) for n in ("dwSize", "dwFlags", "dwXpos", "dwYpos", "dwZpos", "dwRpos", "dwUpos", "dwVpos",
                                                    "dwButtons", "dwButtonNumber", "dwPOV", "dwReserved1", "dwReserved2")]
    winmm = ctypes.WinDLL("winmm")

    def pulsanti():
        """Insieme dei pulsanti premuti (numeri da 1) su tutti i controller collegati."""
        premuti = set()
        for jid in range(16):
            info = JOYINFOEX()
            info.dwSize = ctypes.sizeof(JOYINFOEX)
            info.dwFlags = 0xFF
            if winmm.joyGetPosEx(jid, ctypes.byref(info)) == 0:
                b = info.dwButtons
                premuti.update(i + 1 for i in range(32) if b & (1 << i))
        return premuti
    return pulsanti


class Ptt:
    AZIONI = ("avanti", "indietro", "ripeti", "voce")

    def __init__(self, tasto=0, pulsanti=None, azioni=None):
        self.azioni = {a: int(n) for a, n in (azioni or {}).items() if a in self.AZIONI and n}
        self.conta = {a: 0 for a in self.AZIONI}   # quante volte è stato premuto il tasto dell'azione
        self.assegna = None                          # azione in attesa del prossimo tasto premuto
        self.assegnato = None                        # (azione, tasto) appena assegnato, da salvare
        self._prima = set()
        self.tasto = int(tasto or 0)
        self.premuto = False
        self.ultimi = []           # ultimi pulsanti visti premuti (serve per scegliere il tasto)
        self._pulsanti = pulsanti
        self._attivo = False

    def avvia(self):
        if self._pulsanti is None:
            if not sys.platform.startswith("win"):
                return False
            try:
                self._pulsanti = _lettore_windows()
            except Exception:
                return False
        self._attivo = True
        threading.Thread(target=self._ciclo, daemon=True).start()
        return True

    def _ciclo(self):
        while self._attivo:
            self.passo()
            time.sleep(0.01)

    def passo(self):
        try:
            p = self._pulsanti()
        except Exception:
            p = set()
        if p:
            self.ultimi = sorted(p)
        nuovi = p - self._prima
        self._prima = set(p)
        for n in sorted(nuovi):
            if self.assegna:
                self.azioni = {a: t for a, t in self.azioni.items() if t != n and a != self.assegna}
                self.azioni[self.assegna] = n
                self.assegnato = (self.assegna, n)
                self.assegna = None
                break
            for a, t in self.azioni.items():
                if t == n:
                    self.conta[a] += 1
        self.premuto = bool(self.tasto and self.tasto in p)



# Telecomando: tasti del tastierino numerico letti anche quando Simapex non è la finestra attiva
# (Bloc Num acceso). Nome -> codice virtuale di Windows.
TASTI_TELECOMANDO = {"n0": 0x60, "n1": 0x61, "n2": 0x62, "n3": 0x63, "n4": 0x64, "n5": 0x65, "n6": 0x66,
                     "n7": 0x67, "n8": 0x68, "n9": 0x69, "mul": 0x6A, "add": 0x6B, "sub": 0x6D, "dec": 0x6E, "div": 0x6F}


def _lettore_tastiera():
    import ctypes
    u = ctypes.WinDLL("user32")
    u.GetAsyncKeyState.argtypes = [ctypes.c_int]
    u.GetAsyncKeyState.restype = ctypes.c_short

    def premuti():
        return {n for n, vk in TASTI_TELECOMANDO.items() if u.GetAsyncKeyState(vk) & 0x8000}
    return premuti


class Tastiera:
    def __init__(self, premuti=None):
        self._premuti = premuti
        self.conta = {n: 0 for n in TASTI_TELECOMANDO}
        self._prima = set()
        self._attivo = False

    def avvia(self):
        if self._premuti is None:
            if not sys.platform.startswith("win"):
                return False
            try:
                self._premuti = _lettore_tastiera()
            except Exception:
                return False
        self._attivo = True
        threading.Thread(target=self._ciclo, daemon=True).start()
        return True

    def _ciclo(self):
        while self._attivo:
            self.passo()
            time.sleep(0.015)

    def passo(self):
        try:
            p = set(self._premuti())
        except Exception:
            p = set()
        for n in p - self._prima:
            self.conta[n] += 1
        self._prima = p
