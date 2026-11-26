import datetime
from simapex import calendario as c

HTML = '''<div class="rounded-2 mb-2"><time datetime="2026-11-27T20:10:00Z">x</time> <a href="/championships/27423">4FUN - GT4 50 minuti di Laguna Seca</a> ACC - PC ROMAGNOLI ESPORTS ASD</div>
<div class="rounded-2 mb-2"><time datetime="2026-11-28T10:00:00Z">x</time> <a href="/championships/1">Endurance GT3 3 ore</a> ACC - CROSSPLAY Boh</div>
<div class="rounded-2 mb-2"><time datetime="2026-11-27T20:10:00Z">x</time> <a href="/championships/2">F1 25 gara</a> F1 25 - PC Altri</div>'''


def test_parse_e_etichette():
    ev = c.parse(HTML)
    assert len(ev) == 2 and ev[0]["italiana"] and ev[0]["quando"] == "2026-11-27 21:10"
    assert c.etichetta(ev[0]) == "fattibile"
    assert c.etichetta(ev[1]) == "fuori orario"
    assert c.durata_min("GT3 3 ore") == 180
    f = c.filtra(ev, adesso=datetime.datetime(2026, 11, 26, 12, 0))
    assert f[0]["nome"].startswith("4FUN")


def test_calendario(tmp_path):
    p = c.proponi_prossima(str(tmp_path), "Ferrari", "Misano", "5 giri puliti", datetime.datetime(2026, 11, 26, 22, 0))
    assert p["quando"] == "2026-11-27 21:00"
    p2 = c.proponi_prossima(str(tmp_path), "Ferrari", "Misano", "x", datetime.datetime(2026, 11, 26, 22, 0))
    assert p2["quando"] == "2026-11-28 21:00"
    c.segna_fatto(str(tmp_path), p["id"])
    c.togli(str(tmp_path), p2["id"])
    assert len(c.carica(str(tmp_path))) == 1
