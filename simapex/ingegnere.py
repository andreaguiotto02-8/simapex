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
                 ("safety_car", "Safety car"), ("blocchi", "Blocchi in frenata in questa sessione")):
        if d.get(k) not in (None, "", []):
            r.append("%s: %s" % (n, d[k]))
    if d.get("sessione") in TIPI:
        r.append("Sessione: %s" % TIPI[d["sessione"]])
    return "\n".join(r) or "Nessun dato in diretta (gioco non collegato)."


def rispondi(chiave, domanda, dati):
    domanda = str(domanda or "").strip()[:500]
    if not domanda:
        raise RuntimeError("Scrivi una domanda.")
    testo, _ = claude_api.chiedi(chiave, "Dati in diretta:\n%s\n\nDomanda del pilota: %s" % (contesto(dati or {}), domanda),
                                 sistema=SISTEMA, max_token=300)
    return testo.strip()
