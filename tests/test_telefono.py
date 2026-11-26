import json, tempfile, time, unittest
from simapex import telefono, community


class T(unittest.TestCase):
    def test_riassunto(self):
        with tempfile.TemporaryDirectory() as c:
            community.salva(c, "A", "P", 90000, 95000, 100000)
            giri = [{"auto": "A", "pista": "P", "tempo_ms": 96000, "ts": time.time()}, {"auto": "A", "pista": "P", "tempo_ms": 97500, "ts": time.time()}]
            d = telefono.costruisci(c, giri, "1.0")
            self.assertEqual(d["piste"][0]["migliore_ms"], 96000)
            self.assertEqual(d["piste"][0]["community"]["primo_ms"], 90000)
            json.dumps(d)
            self.assertEqual(telefono.costruisci(c, [], "1.0")["piste"], [])
