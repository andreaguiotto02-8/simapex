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
MAX_MODIFICHE_BASE = 30
MAX_CLICK_BASE = 12
MAX_CLICK_PRESSIONE_BASE = 15

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


def valida_modifiche(setup, modifiche, base=False):
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
        if base:
            massimo = MAX_CLICK_PRESSIONE_BASE if "tyrePressure" in perc else MAX_CLICK_BASE
        else:
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
        if len(valide) >= (MAX_MODIFICHE_BASE if base else MAX_MODIFICHE):
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
    "parametro (5 per le pressioni). Un click di pressione = 0,1 psi circa. Le pressioni ideali a caldo sono 26,4-27,0 psi: se i dati mostrano valori fuori da questo intervallo, correggili. Non toccare niente che non sia nell'elenco "
    "dei parametri modificabili. ABS, controllo trazione (TC1 e TC2) e mappa motore NON puoi modificarli: li regola solo il pilota. Se pensi che cambiarne uno sia utile, scrivilo nel campo \"suggerimenti_pilota\" (lista di frasi semplici, anche vuota), senza metterlo tra le modifiche."
    " Se i dati non bastano per cambiare qualcosa con sicurezza, proponi una sola modifica "
    "prudente oppure nessuna e spiega cosa serve. Rispondi SOLO con un JSON, senza testo fuori dal JSON, in questa forma: "
    '{"problema":"frase breve","spiegazione":"2-4 frasi semplici in italiano, senza gergo","cosa_aspettarsi":"cosa deve '
    'sentire il pilota","modifiche":[{"percorso":"...","click":-1,"motivo":"frase breve"}],"suggerimenti_pilota":[]}'
)


SISTEMA_BASE = (
    "Sei un ingegnere di pista esperto di Assetto Corsa Competizione (GT3). Parli con un pilota italiano "
    "principiante-intermedio che guida con un volante Logitech G29. Devi creare il suo PRIMO SETUP PERSONALIZZATO: "
    "parti dal setup base di ACC e cambia tutto quello che serve e quanto serve (pressioni gomme, bilanciamento freni, "
    "carico aerodinamico, campanatura, convergenza, barre antirollio, ammortizzatori, differenziale, elettronica...) "
    "per risolvere i problemi che il pilota descrive, adattarlo al suo stile di guida (se i dati dello stile sono "
    "presenti) e renderlo valido sia per qualifica sia per gara, facile da guidare subito. I valori del setup sono "
    "indici interi (click): indica di quanti click spostare ogni valore (positivo o negativo), mai valori assoluti. "
    "Massimo 12 click per parametro (15 per le pressioni; un click di pressione = 0,1 psi circa). Usa solo i parametri "
    "dell'elenco. Le pressioni gomme sono SEMPRE da sistemare nel setup base: l'obiettivo a CALDO è 26,4-27,0 psi (le pressioni del setup sono a freddo e in guida salgono di circa 1 psi), segui le indicazioni sulle pressioni che trovi nei dati. Cambia solo ciò che ha un motivo chiaro. Il bilanciamento freni (brakeBias) va SEMPRE valutato e di "
    "solito regolato subito nel setup base. ABS, controllo trazione (TC1 e TC2) e mappa motore NON puoi modificarli: "
    "li regola solo il pilota; se pensi sia utile cambiarne uno scrivilo nel campo \"suggerimenti_pilota\" (lista di frasi "
    "semplici, anche vuota), senza metterlo tra le modifiche. Rispondi SOLO con un JSON, senza testo fuori dal JSON: "
    '{"problema":"frase breve","spiegazione":"4-8 frasi semplici in italiano, senza gergo","cosa_aspettarsi":"cosa deve '
    'sentire il pilota","modifiche":[{"percorso":"...","click":-1,"motivo":"frase breve"}],"suggerimenti_pilota":[]}. Sii compatto: massimo 25 modifiche, ogni motivo di al massimo 12 parole.'
)


def costruisci_domanda(setup, sensazioni, riepilogo_gomme, quaderno_recente, auto, pista, stile=None, extra=None):
    righe = ["Auto: %s - Pista: %s" % (auto, pista), "", "Sensazioni del pilota:", sensazioni.strip() or "(nessuna)", ""]
    if stile:
        righe += ["Stile di guida del pilota (medie sui suoi ultimi giri puliti; valori 0-1 tranne dove indicato): "
                  "freno_medio, tempo_in_frenata, frenata_con_sterzo (quanto frena mentre sterza), gas_pieno, coasting "
                  "(tempo senza gas né freno), nervosismo_sterzo e nervosismo_gas (più alti = più movimenti bruschi), "
                  "costanza_tempi_ms (differenza fra giro migliore e peggiore).", json.dumps(stile, ensure_ascii=False), ""]
    if riepilogo_gomme:
        righe += ["Dati gomme misurati in guida (media sui giri guidati):", json.dumps(riepilogo_gomme, ensure_ascii=False), ""]
    if quaderno_recente:
        righe += ["Modifiche già provate in precedenza su questa auto/pista (più recenti):",
                  json.dumps(quaderno_recente, ensure_ascii=False), ""]
    if extra:
        righe += [extra, ""]
    el = (setup.get("basicSetup") or {}).get("electronics")
    if isinstance(el, dict):
        righe += ["Elettronica attuale (SOLA LETTURA, la regola il pilota): " + json.dumps(el), ""]
    righe += ["Parametri modificabili con il valore attuale (percorso: valore):"]
    righe += ["%s: %s" % (p, v) for p, v in valori_modificabili(setup)]
    return "\n".join(righe)


def estrai_json(testo):
    testo = testo.strip()
    testo = re.sub(r"^```(?:json)?|```$", "", testo, flags=re.M).strip()
    i, f = testo.find("{"), testo.rfind("}")
    if i < 0 or f < 0:
        raise ValueError("risposta senza JSON")
    try:
        return json.loads(testo[i:f + 1])
    except ValueError:
        return _ripara(testo[i:])


def _ripara(testo):
    """Se la risposta è stata tagliata a metà, recupera le modifiche complete già scritte."""
    k = testo.find('"modifiche"')
    if k < 0:
        raise ValueError("risposta incompleta")
    testa = testo[:k].rstrip().rstrip(",")
    try:
        r = json.loads(testa + "}")
    except ValueError:
        r = {}
    dec = json.JSONDecoder()
    j = testo.find("[", k) + 1
    mod = []
    while True:
        j = testo.find("{", j)
        if j < 0:
            break
        try:
            o, fine = dec.raw_decode(testo, j)
        except ValueError:
            break
        mod.append(o)
        j = fine
    if not mod:
        raise ValueError("risposta incompleta")
    r["modifiche"] = mod
    return r


def proponi(chiave, setup, sensazioni, riepilogo_gomme, quaderno_recente, auto, pista, modello=None, base=False, stile=None, log=None, extra=None):
    domanda = costruisci_domanda(setup, sensazioni, riepilogo_gomme, quaderno_recente, auto, pista, stile, extra)
    testo, uso = claude_api.chiedi(chiave, domanda, modello or claude_api.MODELLO,
                                   sistema=SISTEMA_BASE if base else SISTEMA, max_token=6000 if base else 2500, tempo_max=120 if base else 60)
    try:
        r = estrai_json(testo)
    except ValueError:
        if log:
            log("risposta Claude non leggibile (%s): %s" % (uso.get("stop_reason"), testo[:1500]))
        raise RuntimeError("Claude ha risposto in un formato che non capisco. Riprova.")
    valide, scartate = valida_modifiche(setup, r.get("modifiche", []), base)
    return {"problema": str(r.get("problema", ""))[:200], "spiegazione": str(r.get("spiegazione", ""))[:800],
            "cosa_aspettarsi": str(r.get("cosa_aspettarsi", ""))[:400], "modifiche": valide,
            "suggerimenti_pilota": [str(x)[:200] for x in (r.get("suggerimenti_pilota") or [])[:4]] if isinstance(r.get("suggerimenti_pilota"), list) else [],
            "scartate": len(scartate), "token": uso}
