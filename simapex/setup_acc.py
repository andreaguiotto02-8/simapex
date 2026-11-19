# -*- coding: utf-8 -*-
"""Trova e legge i file dei setup salvati da ACC (solo lettura)."""
import datetime
import json
import os
import sys

SOTTO = os.path.join("Assetto Corsa Competizione", "Setups")


def cartelle_candidate():
    env = os.environ.get("SIMAPEX_DOCUMENTI")
    if env:
        return [env]
    c = []
    if sys.platform.startswith("win"):
        try:
            import ctypes
            buf = ctypes.create_unicode_buffer(260)
            ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buf)  # CSIDL_PERSONAL
            if buf.value:
                c.append(buf.value)
        except Exception:
            pass
    home = os.path.expanduser("~")
    for nome in ("Documents", "Documenti"):
        c.append(os.path.join(home, nome))
        c.append(os.path.join(home, "OneDrive", nome))
    return c


def trova_cartella_setup():
    for base in cartelle_candidate():
        p = os.path.join(base, SOTTO)
        if os.path.isdir(p):
            return p
    return None


def elenco_setup(cartella=None):
    cartella = cartella or trova_cartella_setup()
    if not cartella:
        return {"cartella": None, "file": []}
    file = []
    for radice, _, nomi in os.walk(cartella):
        for n in nomi:
            if not n.lower().endswith(".json"):
                continue
            p = os.path.join(radice, n)
            rel = os.path.relpath(p, cartella).split(os.sep)
            auto = rel[0] if len(rel) >= 3 else ""
            pista = rel[1] if len(rel) >= 3 else ""
            valido, nome_auto = False, ""
            try:
                with open(p, "r", encoding="utf-8-sig") as f:
                    d = json.load(f)
                nome_auto = str(d.get("carName", ""))
                valido = isinstance(d, dict) and "basicSetup" in d
            except Exception:
                pass
            st = os.stat(p)
            file.append({
                "auto": auto, "pista": pista, "nome": n, "auto_nel_file": nome_auto, "valido": valido,
                "modificato": datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M"),
            })
    file.sort(key=lambda x: x["modificato"], reverse=True)
    return {"cartella": cartella, "file": file}
