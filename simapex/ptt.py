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
    def __init__(self, tasto=0, pulsanti=None):
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
            time.sleep(0.03)

    def passo(self):
        try:
            p = self._pulsanti()
        except Exception:
            p = set()
        if p:
            self.ultimi = sorted(p)
        self.premuto = bool(self.tasto and self.tasto in p)
