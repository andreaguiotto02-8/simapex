# -*- coding: utf-8 -*-
"""Ingegnere di pista: risponde a una domanda del pilota usando i dati in diretta (Claude, a pagamento, chiave sul PC)."""
from . import claude_api

SISTEMA = ("Sei l'ingegnere di pista di un pilota italiano di simulatori (Assetto Corsa Competizione GT3 oppure F1 25). "
           "Rispondi in italiano semplice, in massimo 3 frasi brevi, come alla radio: niente elenchi, niente termini difficili. "
           "Usa solo i dati che ricevi; se un dato manca dillo e non inventare. Se la domanda riguarda il setup, rispondi in modo "
           "generale e suggerisci di usare la schermata Setup. ABS, controllo di trazione e mappa motore le cambia solo il pilota: "
           "puoi consigliarli, mai darli per cambiati.")

TIPI = {0: "prove libere", 1: "qualifica", 2: "gara", 3: "giro lanciato"}


def contesto(d):
    """Testo con i dati utili dell'istantanea mandata dalla pagina."""
    r = []
    for k, n in (("gioco", "Gioco"), ("auto", "Auto"), ("pista", "Pista"), ("giri_completati", "Giri fatti"), ("giri_totali", "Giri totali"),
                 ("posizione", "Posizione"), ("ultimo_giro", "Ultimo giro"), ("miglior_giro", "Giro migliore"), ("carburante", "Carburante"),
                 ("consumo_giro", "Consumo a giro"), ("giri_stimati", "Giri che restano col carburante"), ("pressioni", "Pressioni gomme (AS, AD, PS, PD)"),
                 ("temp_gomme", "Temperature gomme (AS, AD, PS, PD)"), ("usura_gomme", "Usura gomme %"), ("mescola", "Mescola"),
                 ("eta_gomme", "Giri delle gomme"), ("temp_aria", "Aria C"), ("temp_asfalto", "Asfalto C"), ("tempo_rimasto_s", "Secondi rimasti"),
                 ("safety_car", "Safety car"), ("meteo", "Meteo"), ("distacco_davanti_ms", "Distacco dalla macchina davanti (ms)"),
                 ("distacco_dietro_ms", "Vantaggio sulla macchina dietro (ms)"), ("ultimo_davanti_ms", "Ultimo giro di quello davanti (ms)"),
                 ("ultimo_dietro_ms", "Ultimo giro di quello dietro (ms)"), ("ers_pct", "Batteria ERS %"), ("setup_f1", "Setup F1 attuale"), ("blocchi", "Blocchi in frenata in questa sessione")):
        if d.get(k) not in (None, "", []):
            r.append("%s: %s" % (n, d[k]))
    if d.get("sessione") in TIPI:
        r.append("Sessione: %s" % TIPI[d["sessione"]])
    return "\n".join(r) or "Nessun dato in diretta (gioco non collegato)."


SISTEMA_PIANO = ("Sei la squadra ai box (ingegnere di pista, ingegnere ai box e meccanici) di un pilota italiano di simulatori "
                 "(Assetto Corsa Competizione GT3 oppure F1 25). Prepari il piano per la prossima uscita in pista. Rispondi in italiano "
                 "semplice, una riga breve per voce (Carburante, Gomme, Mappa motore, Quando spingere, Quando risparmiare), senza "
                 "elenchi puntati e senza termini difficili. Usa solo i dati ricevuti e il piano base; se un numero manca dillo. "
                 "ABS, controllo di trazione e mappa motore le cambia solo il pilota: consigliale, non darle per fatte. "
                 "Le regole esatte del gioco o del server possono cambiare: ricorda di controllarle quando conta.")


def rispondi(chiave, domanda, dati, piano=False):
    domanda = str(domanda or "").strip()[:2500 if piano else 500]
    if not domanda:
        raise RuntimeError("Scrivi una domanda.")
    testo, _ = claude_api.chiedi(chiave, "Dati in diretta:\n%s\n\nDomanda del pilota: %s" % (contesto(dati or {}), domanda),
                                 sistema=SISTEMA_PIANO if piano else SISTEMA, max_token=600 if piano else 300)
    return testo.strip()
