# -*- coding: utf-8 -*-
"""Tasto «parla» sul volante: legge i pulsanti dei controller di Windows (stessi numeri di joy.cpl, partendo da 1)."""
import sys
import threading
import time


def _lettore_windows(tasto_attuale=None):
    """Pulsanti premuti. I tasti della tastiera hanno numero 1000 + codice Windows (es. F9 = 1120) e si leggono solo se scelti come tasto radio."""
    import ctypes

    class JOYINFOEX(ctypes.Structure):
        _fields_ = [(n, ctypes.c_uint32) for n in ("dwSize", "dwFlags", "dwXpos", "dwYpos", "dwZpos", "dwRpos", "dwUpos", "dwVpos",
                                                    "dwButtons", "dwButtonNumber", "dwPOV", "dwReserved1", "dwReserved2")]
    winmm = ctypes.WinDLL("winmm")
    u = ctypes.WinDLL("user32")
    u.GetAsyncKeyState.argtypes = [ctypes.c_int]
    u.GetAsyncKeyState.restype = ctypes.c_short
    stato = {"ids": list(range(16)), "t": 0.0}

    def pulsanti():
        """Insieme dei pulsanti premuti (numeri da 1) su tutti i controller collegati."""
        premuti = set()
        ora = time.time()
        scansione = ora - stato["t"] > 3          # ogni 3 secondi si cercano i controller; negli altri momenti si leggono solo quelli trovati
        trovati = []
        for jid in (range(16) if scansione else stato["ids"]):
            info = JOYINFOEX()
            info.dwSize = ctypes.sizeof(JOYINFOEX)
            info.dwFlags = 0xFF
            if winmm.joyGetPosEx(jid, ctypes.byref(info)) == 0:
                trovati.append(jid)
                b = info.dwButtons
                premuti.update(i + 1 for i in range(32) if b & (1 << i))
        if scansione:
            stato["ids"], stato["t"] = trovati, ora
        try:
            t = int(tasto_attuale()) if tasto_attuale else 0
            if t >= 1000 and u.GetAsyncKeyState(t - 1000) & 0x8000:
                premuti.add(t)
        except Exception:
            pass
        return premuti
    return pulsanti


class Ptt:
    AZIONI = ("avanti", "indietro", "ripeti", "voce", "ok")

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
                self._pulsanti = _lettore_windows(lambda: self.tasto)
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



# Telecomando: frecce, Invio e Cancella letti anche quando Simapex non è la finestra attiva. Si accende con Bloc Maiusc (Caps Lock) o con Ctrl+Alt+K.
# Nome -> codice virtuale di Windows. 
TASTI_TELECOMANDO = {"su": 0x26, "giu": 0x28, "sx": 0x25, "dx": 0x27, "invio": 0x0D, "indietro": 0x08, "canc": 0x2E}
VK_BLOC_MAIUSC = 0x14   # Caps Lock: acceso = telecomando acceso


def _lettore_tastiera():
    import ctypes
    u = ctypes.WinDLL("user32")
    u.GetAsyncKeyState.argtypes = [ctypes.c_int]
    u.GetAsyncKeyState.restype = ctypes.c_short
    u.GetKeyState.argtypes = [ctypes.c_int]
    u.GetKeyState.restype = ctypes.c_short

    stato = {"on": False, "prima": False}

    def combinazione():
        return all(u.GetAsyncKeyState(vk) & 0x8000 for vk in (0x11, 0x12, 0x4B))   # Ctrl + Alt + K

    def acceso():
        return stato["on"] or bool(u.GetKeyState(VK_BLOC_MAIUSC) & 1)

    def premuti():
        c = combinazione()
        if c and not stato["prima"]:      # Ctrl+Alt+K accende e spegne il telecomando (anche sui portatili senza Bloc Scorr)
            stato["on"] = not stato["on"]
        stato["prima"] = c
        if not acceso():
            return set()
        return {n for n, vk in TASTI_TELECOMANDO.items() if u.GetAsyncKeyState(vk) & 0x8000}

    premuti.acceso = acceso
    return premuti


def _gancio_tastiera(tasti, acceso, conta, blocca=None, log=None):
    """Gancio di tastiera a basso livello (solo Windows): quando il telecomando è acceso, frecce, Invio, Cancella
    e Canc vengono lette da Simapex e (se blocca() è vero, cioè con F1 aperto) NON arrivano al gioco. A telecomando spento non tocca niente."""
    import ctypes
    from ctypes import wintypes
    u = ctypes.WinDLL("user32", use_last_error=True)
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    LRESULT = ctypes.c_ssize_t
    PROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
    u.SetWindowsHookExW.argtypes = [ctypes.c_int, PROC, wintypes.HINSTANCE, wintypes.DWORD]
    u.SetWindowsHookExW.restype = wintypes.HHOOK
    u.CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
    u.CallNextHookEx.restype = LRESULT
    k.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
    k.GetModuleHandleW.restype = wintypes.HMODULE
    da_vk = {vk: n for n, vk in tasti.items()}
    giu = set()
    hook = [None]

    def cb(code, wp, lp):
        try:
            if code == 0 and acceso():
                vk = ctypes.cast(lp, ctypes.POINTER(wintypes.DWORD))[0]
                n = da_vk.get(vk)
                if n:
                    if wp in (0x100, 0x104):          # tasto premuto
                        if n not in giu:
                            giu.add(n)
                            conta[n] += 1
                    else:                              # rilasciato
                        giu.discard(n)
                    if blocca is None or blocca():
                        return 1                       # il gioco non lo vede
        except Exception:
            pass
        return u.CallNextHookEx(hook[0], code, wp, lp)
    proc = PROC(cb)

    def ciclo():
        hook[0] = u.SetWindowsHookExW(13, proc, k.GetModuleHandleW(None), 0)
        if not hook[0]:
            if log:
                log("telecomando: gancio tastiera non attivo")
            return
        msg = wintypes.MSG()
        while u.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            u.TranslateMessage(ctypes.byref(msg))
            u.DispatchMessageW(ctypes.byref(msg))
    threading.Thread(target=ciclo, daemon=True).start()
    return proc


class Tastiera:
    def __init__(self, premuti=None):
        self._premuti = premuti
        self.blocca = lambda: True   # il server lo cambia: si bloccano i tasti solo con F1 aperto
        self.conta = {n: 0 for n in TASTI_TELECOMANDO}
        self._prima = set()
        self._attivo = False

    def acceso(self):
        f = getattr(self._premuti, "acceso", None)
        return bool(f()) if f else True

    def avvia(self):
        if self._premuti is None:
            if not sys.platform.startswith("win"):
                return False
            try:
                self._premuti = _lettore_tastiera()
            except Exception:
                return False
        self._attivo = True
        self.gancio = False
        f = getattr(self._premuti, "acceso", None)
        if f and sys.platform.startswith("win"):
            try:
                self._proc = _gancio_tastiera(TASTI_TELECOMANDO, f, self.conta, lambda: self.blocca())
                self.gancio = True
            except Exception:
                self.gancio = False
        if not self.gancio:   # senza gancio si leggono i tasti a intervalli (il gioco li riceve comunque)
            threading.Thread(target=self._ciclo, daemon=True).start()
        else:                 # il gancio conta i tasti; questo ciclo serve solo per Ctrl+Alt+K
            threading.Thread(target=self._ciclo_solo_interruttore, daemon=True).start()
        return True

    def _ciclo_solo_interruttore(self):
        while self._attivo:
            try:
                self._premuti()
            except Exception:
                pass
            time.sleep(0.05)

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
