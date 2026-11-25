import tempfile
from simapex import obiettivi as O


def g(i, t, b=0):
    return {"auto": "A", "pista": "P", "tempo_ms": t, "ts": 1000 + i * 100, "blocchi": [1] * b}


def test_fase1_poi_fase2():
    d = tempfile.mkdtemp()
    assert O.stato(d, [], "A", "P")["fase"] == 1
    giri = [g(i, 95000) for i in range(2)]
    assert O.stato(d, giri, "A", "P")["fase"] == 1
    r = O.carica(d)
    for v in r.values():
        v["obiettivo"]["creato"] = 1150
    O.salva(d, r)
    giri += [g(i, 95000) for i in range(2, 9)]
    o = O.stato(d, giri, "A", "P")
    assert o["fase"] == 2 and o["raggiunto"] is True


def test_non_raggiunto_resta():
    d = tempfile.mkdtemp()
    giri = [g(0, 95000), g(1, 95000)]
    O.stato(d, giri, "A", "P")
    r = O.carica(d)
    for v in r.values():
        v["obiettivo"]["creato"] = 1150
    O.salva(d, r)
    giri += [g(2, 95000), g(3, 99000), g(4, 95000), g(5, 95000)]
    o = O.stato(d, giri, "A", "P")
    assert o["fase"] == 1 and o["raggiunto"] is False
