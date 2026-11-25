# -*- coding: utf-8 -*-
"""Comandi di ACC (volante e tastiera): lettura, copie di sicurezza, ripristino e controllo dei conflitti con i tasti di Simapex.
Il file è Documenti\\Assetto Corsa Competizione\\Config\\controls.json (numeri dei tasti da 0; qui si mostrano da 1, come joy.cpl)."""
import datetime
import hashlib
import json
import os
import shutil

from .setup_acc import cartelle_candidate

SOTTO = os.path.join("Assetto Corsa Competizione", "Config")

# codice del gioco -> (gruppo, nome in italiano). Nomi scritti a mano sul modello del menu «Controlli» di ACC.
ETICHETTE = {
    "GearUp": ("Guida", "Marcia su"), "GearDown": ("Guida", "Marcia giù"),
    "PitLimiter": ("Guida", "Limitatore box"), "Pause": ("Gioco", "Pausa"),
    "IncreaseBrakeBias": ("Regolazioni in auto", "Ripartizione freni +"), "DecreaseBrakeBias": ("Regolazioni in auto", "Ripartizione freni −"),
    "IncreaseTC": ("Regolazioni in auto", "Controllo trazione +"), "DecreaseTC": ("Regolazioni in auto", "Controllo trazione −"),
    "IncreaseTCCut": ("Regolazioni in auto", "Taglio controllo trazione +"), "DecreaseTCCut": ("Regolazioni in auto", "Taglio controllo trazione −"),
    "IncreaseABS": ("Regolazioni in auto", "ABS +"), "DecreaseABS": ("Regolazioni in auto", "ABS −"),
    "IncreaseEngineMap": ("Regolazioni in auto", "Mappa motore +"), "DecreaseEngineMap": ("Regolazioni in auto", "Mappa motore −"),
    "EnableFlashingLights": ("Luci", "Lampeggio fari"), "ToggleWiper": ("Luci", "Tergicristalli on/off"), "CycleWiper": ("Luci", "Tergicristalli velocità"),
    "DisplayPageUp": ("Schermo (MFD)", "Pagina schermo su"), "DisplayPageDown": ("Schermo (MFD)", "Pagina schermo giù"),
    "CycleHudMfd": ("Schermo (MFD)", "Cambia schermo MFD"), "CycleHudMfdPrevious": ("Schermo (MFD)", "Schermo MFD precedente"),
    "CycleCamera": ("Telecamere", "Cambia telecamera"), "IgnitionSequenceOn": ("Guida", "Accensione"), "Starter": ("Guida", "Motorino avviamento"),
    "Up": ("Menu", "Su"), "Down": ("Menu", "Giù"), "Left": ("Menu", "Sinistra"), "Right": ("Menu", "Destra"),
    "Forward": ("Menu", "Avanti / conferma"), "Backward": ("Menu", "Indietro"), "CycleLeft": ("Menu", "Scheda a sinistra"), "CycleRight": ("Menu", "Scheda a destra"),
    "Steer": ("Assi", "Sterzo"), "Gas": ("Assi", "Acceleratore"), "Brake": ("Assi", "Freno"), "Clutch": ("Assi", "Frizione"),
}
ORDINE = ["Assi", "Guida", "Regolazioni in auto", "Schermo (MFD)", "Luci", "Telecamere", "Gioco", "Menu", "Altro"]
# comandi utili che si possono suggerire se mancano (nome del gioco, perché)
IDEE = [("ToggleWiper", "Tergicristalli: utile se piove."), ("IncreaseTCCut", "Taglio controllo trazione +: regola l'uscita di curva."),
        ("DecreaseTCCut", "Taglio controllo trazione −."), ("CycleCamera", "Cambia telecamera (per la prova libera)."),
        ("EnableFlashingLights", "Lampeggio fari per farti dare strada.")]
NUM_TASTI_VOLANTE = 25   # il G29 ha circa 25 tasti utili (più la croce direzionale)


def cartella_controlli():
    for base in cartelle_candidate():
        p = os.path.join(base, SOTTO)
        if os.path.isfile(os.path.join(p, "controls.json")):
            return p
    return None


def _leggi(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def _etichetta(codice):
    g, n = ETICHETTE.get(codice, ("Altro", codice))
    return g, n


def _nome_tasto(e):
    bi, pi, pv = e.get("buttonIndex", -1), e.get("powIndex", -1), e.get("powValue", 0)
    if bi is not None and bi >= 0:
        return "tasto %d" % (bi + 1)
    if pi is not None and pi >= 0:
        dire = {0: "croce su", 9000: "croce destra", 18000: "croce giù", 27000: "croce sinistra"}
        return dire.get(pv, "croce %s" % pv)
    k = e.get("keyName")
    return ("tastiera " + k) if k and k != "None" else "—"


def voci_da_dati(d):
    """Elenco dei comandi: [{gruppo, nome, codice, dispositivo, tasto, numero (se tasto del volante)}]."""
    out = []
    for dev in d.get("commandDevices", []):
        nome_disp = dev.get("productName", "")
        for lista in ("uICommandButtonList", "raceCommandButtonList"):
            for e in dev.get(lista, []):
                for campo in ("instantActionCode", "extendedActionCode", "pinkieInstanceActionCode"):
                    c = e.get(campo)
                    if c and c != "None":
                        g, n = _etichetta(c)
                        if campo != "instantActionCode":
                            n += " (tenuto premuto)" if campo == "extendedActionCode" else " (con tasto secondario)"
                        num = e["buttonIndex"] + 1 if e.get("buttonIndex", -1) >= 0 else None
                        out.append({"gruppo": g, "nome": n, "codice": c, "dispositivo": nome_disp, "tasto": _nome_tasto(e), "numero": num,
                                    "menu": lista == "uICommandButtonList"})
        for e in dev.get("raceCommandAxisList", []):
            c = e.get("axisCode")
            if c and c != "None":
                g, n = _etichetta(c)
                out.append({"gruppo": g, "nome": n, "codice": c, "dispositivo": nome_disp, "tasto": "asse %d" % e.get("axisIndex", 0), "numero": None, "menu": False})
    out.sort(key=lambda v: (ORDINE.index(v["gruppo"]) if v["gruppo"] in ORDINE else 99, v["nome"]))
    return out


def analizza(d, tasti_simapex=None):
    """Voci, tasti liberi del volante, conflitti con i tasti di Simapex e idee."""
    voci = voci_da_dati(d)
    usati = {}
    for v in voci:
        if v["numero"]:
            usati.setdefault(v["numero"], []).append(v["nome"])
    liberi = [n for n in range(1, NUM_TASTI_VOLANTE + 1) if n not in usati]
    conflitti = []
    for az, n in (tasti_simapex or {}).items():
        if n and 0 < n < 1000 and n in usati:
            conflitti.append({"azione": az, "tasto": n, "con": usati[n][0]})
    assegnati = {v["codice"] for v in voci}
    idee = [{"codice": c, "nome": _etichetta(c)[1], "perche": p} for c, p in IDEE if c not in assegnati]
    return {"voci": voci, "liberi": liberi, "conflitti": conflitti, "idee": idee}


def _cartella_copie(base_dati):
    p = os.path.join(base_dati, "comandi")
    os.makedirs(p, exist_ok=True)
    return p


def _impronta(path):
    with open(path, "rb") as f:
        return hashlib.sha1(f.read()).hexdigest()[:10]


def copie(base_dati):
    p = _cartella_copie(base_dati)
    return sorted([f for f in os.listdir(p) if f.startswith("acc_") and f.endswith(".json")], reverse=True)


def salva_copia(base_dati, cartella=None):
    """Copia di sicurezza dei comandi attuali (solo se sono cambiati dall'ultima copia). Ritorna il nome del file o None."""
    cartella = cartella or cartella_controlli()
    if not cartella:
        return None
    src = os.path.join(cartella, "controls.json")
    imp = _impronta(src)
    dest = _cartella_copie(base_dati)
    for f in copie(base_dati):
        if f.endswith("_" + imp + ".json"):
            return None
    nome = "acc_%s_%s.json" % (datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S"), imp)
    shutil.copy2(src, os.path.join(dest, nome))
    for vecchio in copie(base_dati)[40:]:
        try:
            os.remove(os.path.join(dest, vecchio))
        except OSError:
            pass
    return nome


def ripristina(base_dati, nome, gioco_aperto=False, cartella=None):
    """Rimette una copia nel gioco (prima salva quella attuale). Con ACC aperto non si fa: il gioco la sovrascriverebbe."""
    if gioco_aperto:
        return {"ok": False, "errore": "Chiudi prima ACC: se è aperto sovrascrive i comandi."}
    cartella = cartella or cartella_controlli()
    if not cartella:
        return {"ok": False, "errore": "Non trovo i comandi di ACC su questo PC."}
    if nome not in copie(base_dati):
        return {"ok": False, "errore": "Copia non trovata."}
    salva_copia(base_dati, cartella)
    shutil.copy2(os.path.join(_cartella_copie(base_dati), nome), os.path.join(cartella, "controls.json"))
    return {"ok": True}
