# -*- coding: utf-8 -*-
"""Assistente setup: Claude propone poche modifiche, il programma crea un setup NUOVO (mai sovrascrive)."""
import copy
import json
import os
import re
import time

from . import claude_api

MODIFICABILI = (
    "basicSetup.tyres.tyrePressure", "basicSetup.alignment.camber", "basicSetup.alignment.toe",
    "basicSetup.alignment.casterLF", "basicSetup.alignment.casterRF",
    "basicSetup.electronics.tC1", "basicSetup.electronics.tC2", "basicSetup.electronics.abs",
    "basicSetup.electronics.eCUMap",
    "advancedSetup.mechanicalBalance.aRBFront", "advancedSetup.mechanicalBalance.aRBRear",
    "advancedSetup.mechanicalBalance.wheelRate", "advancedSetup.mechanicalBalance.brakeTorque",
    "advancedSetup.mechanicalBalance.brakeBias",
    "advancedSetup.dampers.bumpSlow", "advancedSetup.dampers.bumpFast",
    "advancedSetup.dampers.reboundSlow", "advancedSetup.dampers.reboundFast",
    "advancedSetup.aeroBalance.rideHeight", "advancedSetup.aeroBalance.splitter",
    "advancedSetup.aeroBalance.rearWing", "advancedSetup.aeroBalance.brakeDuct",
    "advancedSetup.drivetrain.preload",
)
MAX_MODIFICHE = 3
MAX_CLICK = 3
MAX_CLICK_PRESSIONE = 5

NOMI = {
    "tyrePressure": "pressione gomme", "camber": "campanatura", "toe": "convergenza",
    "casterLF": "incidenza ant. sinistra", "casterRF": "incidenza ant. destra",
    "tC1": "controllo trazione", "tC2": "taglio controllo trazione", "abs": "ABS", "eCUMap": "mappa motore",
    "aRBFront": "barra antirollio anteriore", "aRBRear": "barra antirollio posteriore",
    "wheelRate": "rigidità molle", "brakeTorque": "potenza freni", "brakeBias": "bilanciamento freni",
    "bumpSlow": "compressione lenta", "bumpFast": "compressione veloce",
    "reboundSlow": "estensione lenta", "reboundFast": "estensione veloce",
    "rideHeight": "altezza da terra", "splitter": "splitter", "rearWing": "ala posteriore",
    "brakeDuct": "condotti freni", "preload": "precarico differenziale",
}
POSIZIONI = ["ant. sx", "ant. dx", "post. sx", "post. dx"]


def valori_modificabili(setup):
    """Elenco (percorso, valore) dei numeri interi che Claude può cambiare."""
    out = []
    for base in MODIFICABILI:
        nodo = setup
        ok = True
        for p in base.split("."):
            if isinstance(nodo, dict) and p in nodo:
                nodo = nodo[p]
            else:
                ok = False
                break
        if not ok:
            continue
        if isinstance(nodo, list):
            for i, v in enumerate(nodo):
                if isinstance(v, int) and not isinstance(v, bool):
                    out.append(("%s[%d]" % (base, i), v))
        elif isinstance(nodo, int) and not isinstance(nodo, bool):
            out.append((base, nodo))
    return out


def _vai(setup, percorso):
    m = re.match(r"^(.*?)(?:\[(\d+)\])?$", percorso)
    base, idx = m.group(1), m.group(2)
    nodo = setup
    parti = base.split(".")
    for p in parti[:-1]:
        nodo = nodo[p]
    return nodo, parti[-1], (int(idx) if idx is not None else None)


def nome_leggibile(percorso):
    m = re.match(r"^(.*?)(?:\[(\d+)\])?$", percorso)
    base = m.group(1).split(".")[-1]
    s = NOMI.get(base, base)
    if m.group(2) is not None:
        i = int(m.group(2))
        if base in ("casterLF", "casterRF", "brakeDuct") or i > 3:
            s += " %d" % (i + 1) if base == "brakeDuct" else ""
        else:
            s += " " + POSIZIONI[i]
    return s


def valida_modifiche(setup, modifiche):
    """Controlla le modifiche proposte. Ritorna (valide, scartate)."""
    consentiti = dict(valori_modificabili(setup))
    valide, scartate, visti = [], [], set()
    for m in modifiche if isinstance(modifiche, list) else []:
        try:
            perc = str(m["percorso"])
            delta = int(m["click"])
        except (KeyError, TypeError, ValueError):
            scartate.append(m)
            continue
        massimo = MAX_CLICK_PRESSIONE if "tyrePressure" in perc else MAX_CLICK
        if perc not in consentiti or perc in visti or delta == 0 or abs(delta) > massimo:
            scartate.append(m)
            continue
        if consentiti[perc] + delta < 0:
            scartate.append(m)
            continue
        visti.add(perc)
        valide.append({"percorso": perc, "click": delta, "motivo": str(m.get("motivo", ""))[:300],
                       "prima": consentiti[perc], "dopo": consentiti[perc] + delta})
        if len(valide) >= MAX_MODIFICHE:
            break
    return valide, scartate


def applica(setup, valide):
    nuovo = copy.deepcopy(setup)
    for m in valide:
        nodo, chiave, idx = _vai(nuovo, m["percorso"])
        if idx is None:
            nodo[chiave] = m["dopo"]
        else:
            nodo[chiave][idx] = m["dopo"]
    return nuovo


def nome_nuovo_file(cartella, nome_originale):
    base = re.sub(r"( - Simapex \d+)?\.json$", "", nome_originale, flags=re.I)
    n = 1
    while os.path.exists(os.path.join(cartella, "%s - Simapex %d.json" % (base, n))):
        n += 1
    return "%s - Simapex %d.json" % (base, n)


SISTEMA = (
    "Sei un ingegnere di pista esperto di Assetto Corsa Competizione (GT3). Parli con un pilota italiano "
    "principiante-intermedio che guida con un volante Logitech G29. Il tuo compito: partendo dal setup attuale, "
    "dalle sue sensazioni e dai dati delle gomme, proponi POCHE modifiche (massimo 3, meglio 1 o 2) per rendere "
    "l'auto più guidabile, risolvendo un problema alla volta. I valori del setup sono indici interi (click): "
    "tu indichi di quanti click spostare ogni valore (positivo o negativo), mai valori assoluti. Massimo 3 click per "
    "parametro (5 per le pressioni). Un click di pressione = 0,1 psi circa. Non toccare niente che non sia nell'elenco "
    "dei parametri modificabili. Se i dati non bastano per cambiare qualcosa con sicurezza, proponi una sola modifica "
    "prudente oppure nessuna e spiega cosa serve. Rispondi SOLO con un JSON, senza testo fuori dal JSON, in questa forma: "
    '{"problema":"frase breve","spiegazione":"2-4 frasi semplici in italiano, senza gergo","cosa_aspettarsi":"cosa deve '
    'sentire il pilota","modifiche":[{"percorso":"...","click":-1,"motivo":"frase breve"}]}'
)


def costruisci_domanda(setup, sensazioni, riepilogo_gomme, quaderno_recente, auto, pista):
    righe = ["Auto: %s - Pista: %s" % (auto, pista), "", "Sensazioni del pilota:", sensazioni.strip() or "(nessuna)", ""]
    if riepilogo_gomme:
        righe += ["Dati gomme misurati in guida (media sui giri guidati):", json.dumps(riepilogo_gomme, ensure_ascii=False), ""]
    if quaderno_recente:
        righe += ["Modifiche già provate in precedenza su questa auto/pista (più recenti):",
                  json.dumps(quaderno_recente, ensure_ascii=False), ""]
    righe += ["Parametri modificabili con il valore attuale (percorso: valore):"]
    righe += ["%s: %s" % (p, v) for p, v in valori_modificabili(setup)]
    return "\n".join(righe)


def estrai_json(testo):
    testo = testo.strip()
    testo = re.sub(r"^```(?:json)?|```$", "", testo, flags=re.M).strip()
    i, f = testo.find("{"), testo.rfind("}")
    if i < 0 or f < 0:
        raise ValueError("risposta senza JSON")
    return json.loads(testo[i:f + 1])


def proponi(chiave, setup, sensazioni, riepilogo_gomme, quaderno_recente, auto, pista, modello=None):
    domanda = costruisci_domanda(setup, sensazioni, riepilogo_gomme, quaderno_recente, auto, pista)
    testo, uso = claude_api.chiedi(chiave, domanda, modello or claude_api.MODELLO, sistema=SISTEMA, max_token=900)
    try:
        r = estrai_json(testo)
    except ValueError:
        raise RuntimeError("Claude ha risposto in un formato che non capisco. Riprova.")
    valide, scartate = valida_modifiche(setup, r.get("modifiche", []))
    return {"problema": str(r.get("problema", ""))[:200], "spiegazione": str(r.get("spiegazione", ""))[:800],
            "cosa_aspettarsi": str(r.get("cosa_aspettarsi", ""))[:400], "modifiche": valide,
            "scartate": len(scartate), "token": uso}
