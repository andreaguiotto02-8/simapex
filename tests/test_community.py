from simapex import community


def test_estrai_e_riassumi():
    t = community.estrai_tempi("<td>1:34.567</td><td>1:35.100</td><td>1:36,000</td><td>1:40.000</td><td>9:99.999</td>")
    assert t[0] == 94567 and len(t) == 4
    r = community.riassunto(t)
    assert r["primo_ms"] == 94567 and r["ultimo_ms"] == 100000


def test_salva_e_percentuale(tmp_path):
    community.salva(str(tmp_path), "Ferrari", "Misano", 94000, 96000, 99000)
    s = community.stato(str(tmp_path), "Ferrari", "Misano", 98000)
    assert s["pct_primo"] == 104.3 and s["pct_mediana"] == 102.1
    assert "mediana" in s["testo"]
    assert community.stato(str(tmp_path), "X", "Y", 1) is None
