# -*- coding: utf-8 -*-
"""Pressioni a caldo: confronto con l'intervallo ideale delle GT3 di ACC e correzione dei click del setup."""
OBIETTIVO = (26.4, 27.0)   # psi a caldo, GT3 in ACC (guide di GoSetups e SimRacingSetup)
CENTRO = 26.7
PSI_PER_CLICK = 0.1
SCARTA_PRIMI = 2           # i primi giri sono ancora freddi
ULTIMI = 4
NOMI = ["ant. sx", "ant. dx", "post. sx", "post. dx"]


def _mediana(v):
    v = sorted(v)
    n = len(v)
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2.0


def a_caldo(giri_sessione):
    """Pressione a caldo per ruota (mediana degli ultimi giri, esclusi i primi). None se i dati non bastano."""
    g = [x["gomme"]["p"] for x in giri_sessione if x.get("gomme") and x["gomme"].get("p")]
    g = g[SCARTA_PRIMI:][-ULTIMI:]
    if len(g) < 2:
        return None
    return [round(_mediana([x[i] for x in g]), 2) for i in range(4)]


def stato(psi):
    return "ok" if OBIETTIVO[0] <= psi <= OBIETTIVO[1] else ("alta" if psi > OBIETTIVO[1] else "bassa")


def click_necessari(psi):
    if stato(psi) == "ok":
        return 0
    return int(round((CENTRO - psi) / PSI_PER_CLICK))


def testo_pressioni(caldo):
    """Una frase per il report."""
    fuori = ["%s %.1f (%s)" % (NOMI[i], caldo[i], "alta" if stato(caldo[i]) == "alta" else "bassa")
             for i in range(4) if stato(caldo[i]) != "ok"]
    base = "Pressioni a caldo (ideale %.1f-%.1f psi): %s." % (OBIETTIVO[0], OBIETTIVO[1], ", ".join("%s %.1f" % (NOMI[i], caldo[i]) for i in range(4)))
    return base + (" Fuori intervallo: " + ", ".join(fuori) + "." if fuori else " Sono tutte nell'intervallo giusto.")


def proposta(giri_sessione, setup_pressioni_valori):
    """Correzione deterministica delle pressioni (senza Claude). setup_pressioni_valori: lista di 4 click attuali."""
    caldo = a_caldo(giri_sessione)
    if caldo is None:
        return {"problema": "Pressioni a caldo", "spiegazione": "Servono almeno 4 giri con questo setup (i primi due non contano, sono ancora freddi). Guida ancora un po' e riprova.",
                "cosa_aspettarsi": "", "modifiche": [], "suggerimenti_pilota": []}
    mod = []
    for i in range(4):
        c = max(-15, min(15, click_necessari(caldo[i])))
        if c:
            mod.append({"percorso": "basicSetup.tyres.tyrePressure[%d]" % i, "click": c,
                        "motivo": "a caldo %.1f psi, obiettivo %.1f" % (caldo[i], CENTRO)})
    spieg = testo_pressioni(caldo)
    return {"problema": "Correzione pressioni a caldo", "spiegazione": spieg,
            "cosa_aspettarsi": "Dopo 4-5 giri le pressioni a caldo devono stare tra %.1f e %.1f psi." % OBIETTIVO if mod else "Le pressioni sono già giuste: non cambio niente.",
            "modifiche": mod, "suggerimenti_pilota": []}


def info_per_claude(giri_auto):
    """Testo per il setup base: ultime pressioni a caldo misurate con questa auto (se ci sono)."""
    righe = ["Obiettivo pressioni a CALDO per le GT3 in ACC: %.1f-%.1f psi su tutte e quattro le gomme (centro %.1f). "
             "Le pressioni del setup sono a FREDDO: in guida salgono di circa 1 psi. Se non ci sono misure, punta a una pressione a freddo "
             "di circa %.1f psi e non alzarla troppo." % (OBIETTIVO[0], OBIETTIVO[1], CENTRO, CENTRO - 1.0)]
    ultimo = None
    sess = []
    for x in giri_auto:
        if sess and (x.get("pista") != sess[-1].get("pista") or (x.get("ts") or 0) - (sess[-1].get("ts") or 0) > 1200):
            ultimo = sess
            sess = []
        sess.append(x)
    ultimo = sess or ultimo
    c = a_caldo(ultimo) if ultimo else None
    if c:
        righe.append("Ultime pressioni a caldo misurate con questa auto (ant.sx, ant.dx, post.sx, post.dx): %s psi. Correggi i click di conseguenza "
                     "(circa 0,1 psi per click) per portarle al centro dell'intervallo." % c)
    return "\n".join(righe)
