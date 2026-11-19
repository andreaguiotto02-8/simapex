import json
import os
import struct
import tempfile
import threading
import time
import unittest
import urllib.request

from simapex import server, setup_acc, telemetria


def fisica():
    b = bytearray(256)
    struct.pack_into("<i", b, 0, 5)
    struct.pack_into("<f", b, 4, 0.8)
    struct.pack_into("<f", b, 8, 0.1)
    struct.pack_into("<f", b, 12, 42.5)
    struct.pack_into("<i", b, 16, 4)      # 3a marcia
    struct.pack_into("<i", b, 20, 6800)
    struct.pack_into("<f", b, 28, 187.4)
    struct.pack_into("<4f", b, 88, 27.1, 27.2, 26.5, 26.6)
    struct.pack_into("<4f", b, 152, 78.0, 79.5, 75.2, 76.0)
    return bytes(b)


def grafica():
    b = bytearray(256)
    struct.pack_into("<i", b, 4, 2)
    struct.pack_into("<i", b, 132, 3)
    struct.pack_into("<i", b, 144, 118345)
    struct.pack_into("<i", b, 148, 117001)
    return bytes(b)


def statica():
    b = bytearray(256)
    b[68:68 + 2 * 14] = "ferrari_488_gt3"[:14].encode("utf-16-le")
    t = "monza".encode("utf-16-le")
    b[134:134 + len(t)] = t
    return bytes(b)


def finta(nome):
    return {"physics": fisica(), "graphics": grafica(), "static": statica()}.get(nome)


class TestTelemetria(unittest.TestCase):
    def test_lettura(self):
        s = telemetria.Lettore(finta).stato()
        self.assertTrue(s["collegato"])
        self.assertEqual(s["marcia"], "3")
        self.assertAlmostEqual(s["velocita"], 187.4, 1)
        self.assertEqual(s["giri_motore"], 6800)
        self.assertAlmostEqual(s["carburante"], 42.5, 1)
        self.assertEqual(s["pressioni"][0], 27.1)
        self.assertEqual(s["ultimo_giro"], "1:58.345")
        self.assertEqual(s["miglior_giro"], "1:57.001")
        self.assertEqual(s["giri_completati"], 3)
        self.assertEqual(s["pista"], "monza")

    def test_acc_spento(self):
        self.assertFalse(telemetria.Lettore(lambda n: None).stato()["collegato"])

    def test_nessun_crash(self):
        def rotto(n):
            raise OSError("boom")
        s = telemetria.Lettore(rotto).stato()
        self.assertFalse(s["collegato"])
        self.assertIn("errore", s)


class TestSetup(unittest.TestCase):
    def test_elenco(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "ferrari_488_gt3", "monza")
            os.makedirs(p)
            with open(os.path.join(p, "base.json"), "w", encoding="utf-8") as f:
                json.dump({"carName": "ferrari_488_gt3", "basicSetup": {}}, f)
            with open(os.path.join(p, "rotto.json"), "w", encoding="utf-8") as f:
                f.write("{non json")
            r = setup_acc.elenco_setup(d)
            self.assertEqual(len(r["file"]), 2)
            ok = [x for x in r["file"] if x["nome"] == "base.json"][0]
            self.assertTrue(ok["valido"])
            self.assertEqual(ok["auto"], "ferrari_488_gt3")
            self.assertEqual(ok["pista"], "monza")

    def test_cartella_assente(self):
        self.assertEqual(setup_acc.elenco_setup("/non/esiste/mai")["file"], [])


class TestServer(unittest.TestCase):
    def test_api(self):
        server._lettore = telemetria.Lettore(finta)
        server.PORTA = 8799
        server._fermati.clear()
        t = threading.Thread(target=server.main, kwargs={"apri_browser": False}, daemon=True)
        t.start()
        time.sleep(0.8)
        try:
            u = "http://127.0.0.1:8799"
            s = json.loads(urllib.request.urlopen(u + "/api/stato").read())
            self.assertTrue(s["collegato"])
            self.assertIn("versione", s)
            html = urllib.request.urlopen(u + "/").read().decode("utf-8")
            self.assertIn("SIMAPEX", html)
            self.assertNotIn("__VERSIONE__", html)
            json.loads(urllib.request.urlopen(u + "/api/setup").read())
            m = json.loads(urllib.request.urlopen(u + "/manifest.webmanifest").read())
            self.assertEqual(m["name"], "Simapex")
            for p in ("/icona-192.png", "/icona-512.png", "/favicon.ico"):
                r = urllib.request.urlopen(u + p)
                self.assertGreater(len(r.read()), 500)
            self.assertIn("serviceWorker", html)
        finally:
            req = urllib.request.Request("http://127.0.0.1:8799/api/chiudi", method="POST")
            urllib.request.urlopen(req)
            t.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
