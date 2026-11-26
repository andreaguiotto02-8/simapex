# -*- coding: utf-8 -*-
"""Coach di fine sessione: riepilogo breve (dove perdi tempo, UNA curva da migliorare). Mai durante la guida."""
from .telemetria import formatta_tempo


def _parte_giro(i, n=25):
    p = (i + 0.5) / n
    return "all'inizio del giro" if p < 0.2 else "nella prima metà" if p < 0.45 else "a metà giro" if p < 0.6 else "nella seconda metà" if p < 0.85 else "verso la fine del giro"


def riepilogo(sessione, segmenti=None, record_ms=None):
    """sessione: giri della sessione. segmenti: perdita in ms per tratto (25) rispetto al tuo giro migliore, se nota.
    Ritorna dict con 'righe' (max 3 frasi corte) oppure None se i giri sono pochi."""
    if not sessione or len(sessione) < 3:
        return None
    tempi = [g["tempo_ms"] for g in sessione]
    migliore = min(tempi)
    puliti = [g for g in sessione if g["tempo_ms"] <= migliore * 1.07 and len(g.get("blocchi") or []) <= 1]
    righe = ["%d giri, migliore %s, %d puliti." % (len(sessione), formatta_tempo(migliore), len(puliti))]
    if len(puliti) >= 3:
        medi = sorted(g["tempo_ms"] for g in puliti)
        sp = (medi[-1] - medi[0]) / 1000.0
        righe.append("Costanza: %.1f s tra il giro più veloce e il più lento puliti." % sp if sp > 0.8 else "Costanza buona: giri molto simili.")
    bl = {}
    for g in sessione:
        for b in g.get("blocchi") or []:
            bl[b.get("ruota")] = bl.get(b.get("ruota"), 0) + 1
    obiettivo = None
    if segmenti:
        i = max(range(len(segmenti)), key=lambda k: segmenti[k])
        if segmenti[i] >= 20:
            obiettivo = "Da migliorare: tratto %d di 25 (%s), perdi %.1f s rispetto al tuo migliore." % (i + 1, _parte_giro(i, len(segmenti)), segmenti[i] / 1000.0)
    if not obiettivo and sum(bl.values()) >= 3:
        obiettivo = "Da migliorare: %d bloccaggi in frenata, frena un po' meno forte all'inizio." % sum(bl.values())
    if not obiettivo:
        obiettivo = "Da migliorare: restare costante, stessi tempi giro dopo giro."
    righe.append(obiettivo)
    if record_ms:
        righe.append("Distanza dal tempo da raggiungere: %.1f%%." % (migliore * 100.0 / record_ms))
    return {"righe": righe, "migliore": formatta_tempo(migliore), "giri": len(sessione)}
