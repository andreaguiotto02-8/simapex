# -*- coding: utf-8 -*-
"""Lettura della telemetria di ACC (memoria condivisa, solo lettura)."""
import struct
import sys

NOMI_PAGINE = {
    "physics": "Local\\acpmf_physics",
    "graphics": "Local\\acpmf_graphics",
    "static": "Local\\acpmf_static",
}
BYTE_LETTI = 512
BYTE_PAGINA = {"physics": 512, "graphics": 1280, "static": 256}
STATI = {0: "spento", 1: "replay", 2: "in pista", 3: "pausa"}


def leggi_pagina_windows(nome):
    """Apre la pagina SOLO se esiste già (non la crea mai), la copia e la chiude.
    Restituisce i byte oppure None se ACC non è in esecuzione."""
    if not sys.platform.startswith("win"):
        return None
    import ctypes
    from ctypes import wintypes

    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.OpenFileMappingW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
    k.OpenFileMappingW.restype = wintypes.HANDLE
    k.MapViewOfFile.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, ctypes.c_size_t]
    k.MapViewOfFile.restype = ctypes.c_void_p
    k.UnmapViewOfFile.argtypes = [ctypes.c_void_p]
    k.CloseHandle.argtypes = [wintypes.HANDLE]
    FILE_MAP_READ = 0x0004
    h = k.OpenFileMappingW(FILE_MAP_READ, False, NOMI_PAGINE[nome])
    if not h:
        return None
    try:
        p = k.MapViewOfFile(h, FILE_MAP_READ, 0, 0, 0)
        if not p:
            return None
        try:
            return ctypes.string_at(p, BYTE_PAGINA.get(nome, BYTE_LETTI))
        finally:
            k.UnmapViewOfFile(p)
    finally:
        k.CloseHandle(h)


def _testo(b, inizio, n_car):
    raw = b[inizio:inizio + n_car * 2]
    try:
        return raw.decode("utf-16-le", errors="ignore").split("\x00")[0].strip()
    except Exception:
        return ""


def _f(b, off):
    return struct.unpack_from("<f", b, off)[0]


def _i(b, off):
    return struct.unpack_from("<i", b, off)[0]


def _4f(b, off):
    return list(struct.unpack_from("<4f", b, off))


def formatta_tempo(ms):
    if ms is None or ms <= 0 or ms > 36000000:
        return ""
    m, resto = divmod(int(ms), 60000)
    return "%d:%06.3f" % (m, resto / 1000.0)


def decodifica_physics(b):
    marcia = _i(b, 16)
    out = {
        "acceleratore": round(_f(b, 4), 3),
        "freno": round(_f(b, 8), 3),
        "carburante": round(_f(b, 12), 2),
        "marcia": "R" if marcia == 0 else "N" if marcia == 1 else str(marcia - 1),
        "giri_motore": _i(b, 20),
        "sterzo": round(_f(b, 24), 3),
        "velocita": round(_f(b, 28), 1),
        "pressioni": [round(x, 1) for x in _4f(b, 88)],       # psi: AS, AD, PS, PD
        "temp_gomme": [round(x, 1) for x in _4f(b, 152)],     # gradi C
    }
    if len(b) >= 416:  # letture aggiuntive (offset da verificare con guida reale)
        out["vel_ruote"] = [round(x, 2) for x in _4f(b, 104)]   # rad/s
        out["abs"] = round(_f(b, 252), 2)
        out["temp_aria"] = round(_f(b, 288), 1)
        out["temp_asfalto"] = round(_f(b, 292), 1)
        out["temp_freni"] = [round(x, 0) for x in _4f(b, 348)]
        out["temp_zone"] = {"interna": [round(x, 1) for x in _4f(b, 368)],
                            "centro": [round(x, 1) for x in _4f(b, 384)],
                            "esterna": [round(x, 1) for x in _4f(b, 400)]}
    return out


def decodifica_graphics(b):
    ultimo, migliore = _i(b, 144), _i(b, 148)
    out = _decodifica_graphics_base(b, ultimo, migliore)
    if len(b) >= 1220:  # posizione sul giro e coordinate dell'auto (offset da verificare con guida reale)
        out["pos_norm"] = round(_f(b, 248), 5)
        out["in_box"] = bool(_i(b, 160))
        ids = list(struct.unpack_from("<60i", b, 976))
        mio = _i(b, 1216)
        idx = ids.index(mio) if mio in ids else 0
        out["coordinate"] = [round(x, 1) for x in struct.unpack_from("<3f", b, 256 + idx * 12)]
    return out


def _decodifica_graphics_base(b, ultimo, migliore):
    return {
        "stato_codice": _i(b, 4),
        "stato_gioco": STATI.get(_i(b, 4), "?"),
        "sessione": _i(b, 8),
        "giri_completati": _i(b, 132),
        "posizione": _i(b, 136),
        "ultimo_giro_ms": ultimo,
        "miglior_giro_ms": migliore,
        "ultimo_giro": formatta_tempo(ultimo),
        "miglior_giro": formatta_tempo(migliore),
    }


def decodifica_static(b):
    return {"auto": _testo(b, 68, 33), "pista": _testo(b, 134, 33)}


class Lettore:
    def __init__(self, leggi_pagina=None):
        self._leggi = leggi_pagina or leggi_pagina_windows

    def stato(self):
        out = {"collegato": False}
        try:
            fisica = self._leggi("physics")
            if not fisica or len(fisica) < 168:
                return out
            out["collegato"] = True
            out.update(decodifica_physics(fisica))
            grafica = self._leggi("graphics")
            if grafica and len(grafica) >= 152:
                out.update(decodifica_graphics(grafica))
            statica = self._leggi("static")
            if statica and len(statica) >= 200:
                out.update(decodifica_static(statica))
        except Exception as e:  # mai fermare il programma per un errore di lettura
            out["errore"] = "%s: %s" % (type(e).__name__, e)
        return out
