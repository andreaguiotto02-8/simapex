from simapex import coach


def _g(t, bl=0):
    return {"tempo_ms": t, "blocchi": [{"ruota": "ant_sx"}] * bl}


def test_pochi_giri():
    assert coach.riepilogo([_g(95000)]) is None


def test_riepilogo_con_tratto():
    s = [_g(95000), _g(95300), _g(95200), _g(99000)]
    seg = [0] * 25
    seg[11] = 400
    r = coach.riepilogo(s, seg, 93000)
    assert len(r["righe"]) <= 4
    assert any("tratto 12" in x for x in r["righe"])
    assert any("%" in x for x in r["righe"])


def test_senza_segmenti_bloccaggi():
    s = [_g(95000, 2), _g(95100, 1), _g(95200)]
    r = coach.riepilogo(s)
    assert any("bloccaggi" in x for x in r["righe"])
