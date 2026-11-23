# -*- coding: utf-8 -*-
"""Assistente setup per F1 25: il setup non è un file, quindi Claude propone i valori nuovi e il pilota li cambia a mano nel gioco."""
import json

from . import assistente, claude_api

NON_MODIFICABILI = ("carburante a inizio sessione", "zavorra")
MAX_MODIFICHE = 2
MAX_MODIFICHE_BASE = 12
PASSO_MAX = {"int": 6, "decimale": 0.6, "psi": 1.5}
PASSO_MAX_BASE = {"int": 20, "decimale": 1.5, "psi": 3.0}

REGOLE = (
    "Sei l'ingegnere ai box di un pilota italiano che gioca a F1 25 (anche con il pacchetto 2026). Il setup non è un file: il pilota "
    "cambia i valori a mano nel gioco, quindi dai SOLO i valori nuovi precisi, uno per ogni parametro. Usa i nomi dei parametri "
    "ESATTAMENTE come li ricevi. Rispetta i limiti del gioco: se non sei sicuro dei limiti di un parametro, parti dal valore "
    "attuale e fai passi piccoli. ABS, controllo di trazione, mappa motore e miscela li decide solo il pilota: non metterli tra le "
    "modifiche, al massimo consigliali in suggerimenti_pilota. Parla in italiano semplice, senza termini difficili. "
    "Rispondi SOLO con un oggetto JSON: {\"problema\": \"...\", \"spiegazione\": \"...\", \"cosa_aspettarsi\": \"...\", "
    "\"modifiche\": [{\"parametro\": \"nome esatto\", \"a\": numero, \"motivo\": \"...\"}], \"suggerimenti_pilota\": [\"...\"]}. ")
SISTEMA = REGOLE + ("Proponi al massimo 2 modifiche, meglio una sola: la più utile per il problema descritto, tenendo conto di cosa "
                    "è già stato provato e dell'esito. Spiega cosa controllare dopo qualche giro.")
SISTEMA_BASE = REGOLE + ("È la prima messa a punto di questa combinazione pista/condizioni: proponi un setup base completo (fino a 12 "
                         "parametri) adatto alla pista, alle temperature e allo stile del pilota, partendo dai valori attuali. "
                         "Non toccare carburante e zavorra.")


def _tipo(nome, v):
    if "psi" in nome:
        return "psi"
    return "decimale" if isinstance(v, float) else "int"


def valida(setup, modifiche, base=False):
    """Tiene solo le modifiche su parametri veri, con numero, diverse dall'attuale e non esagerate."""
    ok, scartate = [], 0
    limite = PASSO_MAX_BASE if base else PASSO_MAX
    for m in modifiche if isinstance(modifiche, list) else []:
        try:
            nome, a = str(m["parametro"]), m["a"]
        except (KeyError, TypeError):
            scartate += 1
            continue
        if nome not in setup or nome in NON_MODIFICABILI or isinstance(setup[nome], list):
            scartate += 1
            continue
        try:
            a = float(a)
        except (TypeError, ValueError):
            scartate += 1
            continue
        da = setup[nome]
        t = _tipo(nome, da)
        if abs(a - da) < 1e-9 or abs(a - da) > limite[t] or a < 0 and "campanatura" not in nome:
            scartate += 1
            continue
        a = int(round(a)) if t == "int" else round(a, 2 if "campanatura" in nome or "convergenza" in nome else 1)
        ok.append({"parametro": nome, "da": da, "a": a, "motivo": str(m.get("motivo", ""))[:300]})
    return ok[:(MAX_MODIFICHE_BASE if base else MAX_MODIFICHE)], scartate


def valida_pressioni(setup, modifiche):
    return modifiche


def costruisci_domanda(stato, setup, sensazioni, gomme, quaderno, stile, extra=None):
    r = ["Auto: %s - Pista: %s" % (stato.get("auto"), stato.get("pista"))]
    cond = []
    for k, n in (("temp_aria", "aria"), ("temp_asfalto", "asfalto"), ("meteo", "meteo")):
        if stato.get(k) not in (None, ""):
            cond.append("%s %s" % (n, stato[k]))
    if cond:
        r.append("Condizioni: " + ", ".join(cond))
    r += ["", "Sensazioni del pilota:", (sensazioni or "").strip() or "(nessuna)", ""]
    if stile:
        r += ["Stile di guida (medie sui giri puliti): " + json.dumps(stile, ensure_ascii=False), ""]
    if gomme:
        r += ["Dati gomme misurati in guida: " + json.dumps(gomme, ensure_ascii=False), ""]
    if stato.get("usura_gomme"):
        r += ["Usura gomme %: " + json.dumps(stato["usura_gomme"]), ""]
    if quaderno:
        r += ["Modifiche già provate su questa auto/pista (più recenti):", json.dumps(quaderno, ensure_ascii=False), ""]
    if extra:
        r += [extra, ""]
    r += ["Setup attuale (nome: valore):"] + ["%s: %s" % (k, v) for k, v in setup.items()]
    return "\n".join(r)


def proponi(chiave, stato, sensazioni, gomme, quaderno, stile, base=False, log=None, extra=None):
    setup = stato.get("setup_f1") or {}
    domanda = costruisci_domanda(stato, setup, sensazioni, gomme, quaderno, stile, extra)
    testo, uso = claude_api.chiedi(chiave, domanda, claude_api.MODELLO, sistema=SISTEMA_BASE if base else SISTEMA,
                                   max_token=3000 if base else 1500, tempo_max=90 if base else 60)
    try:
        r = assistente.estrai_json(testo)
    except ValueError:
        if log:
            log("F1 setup: risposta non leggibile: %s" % testo[:800])
        raise RuntimeError("Claude ha risposto in un formato che non capisco. Riprova.")
    valide, scartate = valida(setup, r.get("modifiche", []), base)
    sug = r.get("suggerimenti_pilota")
    return {"problema": str(r.get("problema", ""))[:200], "spiegazione": str(r.get("spiegazione", ""))[:800],
            "cosa_aspettarsi": str(r.get("cosa_aspettarsi", ""))[:400], "modifiche": valide, "scartate": scartate,
            "suggerimenti_pilota": [str(x)[:200] for x in sug[:4]] if isinstance(sug, list) else []}


def applicato(voce, setup, tol=0.051):
    """True se il setup attuale nel gioco contiene già tutti i valori proposti."""
    try:
        return all(abs(float(setup[m["parametro"]]) - float(m["a"])) <= tol for m in voce.get("modifiche", []))
    except (KeyError, TypeError, ValueError):
        return False
