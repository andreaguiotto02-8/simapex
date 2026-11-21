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
            js = urllib.request.urlopen(u + "/app.js").read().decode("utf-8")
            self.assertIn("serviceWorker", js)
            self.assertIn("--ac", urllib.request.urlopen(u + "/app.css").read().decode("utf-8"))
            for p in ("/api/sessioni", "/api/report", "/api/pista?nome=x", "/api/sessione?id=1"):
                json.loads(urllib.request.urlopen(u + p).read())
        finally:
            req = urllib.request.Request("http://127.0.0.1:8799/api/chiudi", method="POST")
            urllib.request.urlopen(req)
            t.join(timeout=3)


class TestInvio(unittest.TestCase):
    def test_invio_a_github_finto(self):
        import base64
        from http.server import BaseHTTPRequestHandler, HTTPServer
        from simapex import invio
        archivio = {}

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _r(self, c, d):
                b = json.dumps(d).encode()
                self.send_response(c)
                self.send_header("Content-Length", str(len(b)))
                self.end_headers()
                self.wfile.write(b)

            def do_GET(self):
                if "/releases/latest" in self.path:
                    return self._r(200, {"tag_name": "v9.9.9"})
                if self.headers.get("Authorization") != "Bearer buona":
                    return self._r(401, {})
                self._r(404, {})

            def do_PUT(self):
                if self.headers.get("Authorization") != "Bearer buona":
                    return self._r(401, {})
                n = int(self.headers["Content-Length"])
                c = json.loads(self.rfile.read(n))
                archivio[self.path] = base64.b64decode(c["content"]).decode()
                self._r(201, {})

        srv = HTTPServer(("127.0.0.1", 8798), H)
        th = threading.Thread(target=srv.serve_forever, daemon=True)
        th.start()
        os.environ["SIMAPEX_GH_API"] = "http://127.0.0.1:8798"
        try:
            invio.invia_risultati("a/b", "buona", {"prove": [1]}, {"x": 2})
            self.assertEqual(len(archivio), 2)
            self.assertTrue(any("pc/diag.json" in k for k in archivio))
            with self.assertRaises(RuntimeError) as cm:
                invio.invia_risultati("a/b", "sbagliata", {}, {})
            self.assertIn("chiave", str(cm.exception))
            self.assertTrue(invio.controlla_aggiornamenti("0.2.0")["disponibile"])
        finally:
            srv.shutdown()
            os.environ.pop("SIMAPEX_GH_API", None)


class TestAggiorna(unittest.TestCase):
    def test_non_aggiorna_fuori_dal_programma(self):
        from simapex import aggiorna
        self.assertFalse(aggiorna.prova("0.0.1"))
        aggiorna.pulisci_vecchi()


class TestClaudeApi(unittest.TestCase):
    def test_chiamata_finta(self):
        from http.server import BaseHTTPRequestHandler, HTTPServer
        from simapex import claude_api

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_POST(self):
                n = int(self.headers["Content-Length"])
                self.rfile.read(n)
                if self.headers.get("x-api-key") != "sk-ant-ok":
                    self.send_response(401)
                    self.send_header("Content-Length", "2")
                    self.end_headers()
                    self.wfile.write(b"{}")
                    return
                b = json.dumps({"content": [{"type": "text", "text": "Pronto!"}], "usage": {"input_tokens": 5, "output_tokens": 2}}).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(b)))
                self.end_headers()
                self.wfile.write(b)

        srv = HTTPServer(("127.0.0.1", 8796), H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        os.environ["SIMAPEX_CLAUDE_API"] = "http://127.0.0.1:8796"
        try:
            self.assertEqual(claude_api.chiedi("sk-ant-ok", "ciao")[0], "Pronto!")
            with self.assertRaises(RuntimeError) as cm:
                claude_api.chiedi("sk-ant-no", "ciao")
            self.assertIn("chiave", str(cm.exception))
        finally:
            srv.shutdown()
            os.environ.pop("SIMAPEX_CLAUDE_API", None)


class TestAssistente(unittest.TestCase):
    SETUP = {"carName": "x", "basicSetup": {"tyres": {"tyreCompound": 0, "tyrePressure": [45, 45, 41, 41]},
             "alignment": {"camber": [8, 8, 5, 5], "toe": [21, 21, 52, 52], "staticCamber": [-4.3, -4.3, -4.9, -4.9], "casterLF": 14, "casterRF": 14},
             "electronics": {"tC1": 2, "tC2": 0, "abs": 1, "eCUMap": 1}, "strategy": {"fuel": 48}},
             "advancedSetup": {"mechanicalBalance": {"aRBFront": 4, "brakeBias": 45}, "dampers": {"bumpSlow": [8, 8, 5, 5]},
             "aeroBalance": {"rodLength": [54.3, 54.3, 53.1, 53.1], "rearWing": 12}, "drivetrain": {"preload": 5}}}

    def test_validazione(self):
        from simapex import assistente as a
        prop = [{"percorso": "basicSetup.tyres.tyrePressure[0]", "click": -4, "motivo": "a"},
                {"percorso": "basicSetup.strategy.fuel", "click": 5},
                {"percorso": "basicSetup.alignment.staticCamber[0]", "click": 1},
                {"percorso": "advancedSetup.aeroBalance.rearWing", "click": 9},
                {"percorso": "advancedSetup.drivetrain.preload", "click": -9},
                {"percorso": "advancedSetup.mechanicalBalance.aRBFront", "click": 1},
                {"percorso": "advancedSetup.mechanicalBalance.brakeBias", "click": 1},
                {"percorso": "basicSetup.electronics.abs", "click": 1}]
        valide, scartate = a.valida_modifiche(self.SETUP, prop)
        self.assertEqual([m["percorso"] for m in valide], ["basicSetup.tyres.tyrePressure[0]",
                         "advancedSetup.mechanicalBalance.aRBFront", "advancedSetup.mechanicalBalance.brakeBias"])
        nuovo = a.applica(self.SETUP, valide)
        self.assertEqual(nuovo["basicSetup"]["tyres"]["tyrePressure"], [41, 45, 41, 41])
        self.assertEqual(self.SETUP["basicSetup"]["tyres"]["tyrePressure"][0], 45)
        self.assertNotIn("basicSetup.electronics.abs", [p for p, _ in a.valori_modificabili(self.SETUP)])
        self.assertEqual(a.nome_leggibile("basicSetup.tyres.tyrePressure[2]"), "pressione gomme post. sx")

    def test_endpoint_crea_setup_nuovo_senza_toccare_l_originale(self):
        import urllib.request
        from http.server import BaseHTTPRequestHandler, HTTPServer
        risposta = {"problema": "Sottosterzo", "spiegazione": "Prova", "cosa_aspettarsi": "Più presa",
                    "modifiche": [{"percorso": "basicSetup.tyres.tyrePressure[0]", "click": -2, "motivo": "m"}]}

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_POST(self):
                self.rfile.read(int(self.headers["Content-Length"]))
                b = json.dumps({"content": [{"type": "text", "text": "```json\n" + json.dumps(risposta) + "\n```"}], "usage": {}}).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(b)))
                self.end_headers()
                self.wfile.write(b)

        srv = HTTPServer(("127.0.0.1", 8795), H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        doc = tempfile.mkdtemp()
        dati = tempfile.mkdtemp()
        cart = os.path.join(doc, "Assetto Corsa Competizione", "Setups", "auto_x", "monza")
        os.makedirs(cart)
        originale = os.path.join(cart, "base.json")
        with open(originale, "w") as f:
            json.dump(self.SETUP, f)
        prima = open(originale).read()
        os.environ.update(SIMAPEX_DOCUMENTI=doc, SIMAPEX_CLAUDE_API="http://127.0.0.1:8795", LOCALAPPDATA=dati)
        try:
            server.salva_impostazioni({"claude_key": "sk-ant-x"})
            t = threading.Thread(target=server.main, kwargs={"apri_browser": False}, daemon=True)
            t.start()
            time.sleep(0.8)
            u = "http://127.0.0.1:8765"
            req = urllib.request.Request(u + "/api/assistente/proponi", method="POST",
                                         data=json.dumps({"file": "auto_x/monza/base.json", "sensazioni": "sottosterza"}).encode())
            j = json.loads(urllib.request.urlopen(req).read())
            self.assertTrue(j["ok"], j)
            self.assertEqual(j["nuovo_file"], "base - Simapex 1.json")
            self.assertEqual(open(originale).read(), prima)
            nuovo = json.load(open(os.path.join(cart, "base - Simapex 1.json")))
            self.assertEqual(nuovo["basicSetup"]["tyres"]["tyrePressure"][0], 43)
            req = urllib.request.Request(u + "/api/assistente/esito", method="POST", data=json.dumps({"id": j["id"], "esito": "meglio"}).encode())
            self.assertTrue(json.loads(urllib.request.urlopen(req).read())["ok"])
            self.assertEqual(server.carica_quaderno()[-1]["esito"], "meglio")
            bad = urllib.request.Request(u + "/api/assistente/proponi", method="POST", data=json.dumps({"file": "../../x.json"}).encode())
            self.assertFalse(json.loads(urllib.request.urlopen(bad).read())["ok"])
        finally:
            urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:8765/api/chiudi", method="POST"))
            time.sleep(0.5)
            srv.shutdown()
            for k in ("SIMAPEX_DOCUMENTI", "SIMAPEX_CLAUDE_API", "LOCALAPPDATA"):
                os.environ.pop(k, None)


class TestStile(unittest.TestCase):
    def test_registra_giri_e_profilo(self):
        from simapex.stile import RegistroStile
        f = os.path.join(tempfile.mkdtemp(), "stile.json")
        r = RegistroStile(f)

        def campione(giri, i):
            return {"collegato": True, "auto": "a", "pista": "p", "giri_completati": giri, "velocita": 120,
                    "freno": 0.5 if i % 4 == 0 else 0.0, "acceleratore": 1.0 if i % 4 else 0.0,
                    "sterzo": 0.1 if i % 3 == 0 else 0.0, "ultimo_giro_ms": 90000 + giri * 100}
        for giro in range(0, 5):
            for i in range(300):
                r.alimenta(campione(giro, i))
        r.alimenta(campione(5, 0))
        self.assertEqual(len(r.giri), 5)
        p = r.profilo("a", "p")
        self.assertIsNotNone(p)
        self.assertGreater(p["gas_pieno"], 0.5)
        self.assertEqual(len(RegistroStile(f).giri), 5)
        self.assertIsNone(RegistroStile(os.path.join(tempfile.mkdtemp(), "x.json")).profilo())

    def test_modo_base_accetta_piu_modifiche(self):
        from simapex import assistente as a
        prop = [{"percorso": "basicSetup.tyres.tyrePressure[%d]" % i, "click": -10, "motivo": "x"} for i in range(2)]
        prop.append({"percorso": "advancedSetup.aeroBalance.rearWing", "click": 6, "motivo": "x"})
        self.assertEqual(len(a.valida_modifiche(TestAssistente.SETUP, prop)[0]), 0)
        self.assertEqual(len(a.valida_modifiche(TestAssistente.SETUP, prop, True)[0]), 3)


class TestBlocchiReport(unittest.TestCase):
    def test_ruota_bloccata(self):
        from simapex.stile import ruota_bloccata
        d = {"vel_ruote": [80, 80, 80, 80], "freno": 0.9, "velocita": 200}
        self.assertIsNone(ruota_bloccata(d))
        d["vel_ruote"] = [80, 30, 80, 80]
        self.assertEqual(ruota_bloccata(d), 1)
        d["freno"] = 0.0
        self.assertIsNone(ruota_bloccata(d))
        self.assertIsNone(ruota_bloccata({"vel_ruote": [0, 0, 0, 0], "freno": 1, "velocita": 100}))

    def test_decodifica_estesa_e_report(self):
        import struct
        from simapex.telemetria import decodifica_physics
        from simapex.stile import RegistroStile
        from simapex.report import crea_report
        b = bytearray(512)
        struct.pack_into("<4f", b, 104, 70, 71, 72, 73)
        struct.pack_into("<4f", b, 368, 90, 90, 90, 90)
        struct.pack_into("<4f", b, 384, 80, 80, 80, 80)
        struct.pack_into("<4f", b, 400, 70, 70, 70, 70)
        d = decodifica_physics(bytes(b))
        self.assertEqual(d["vel_ruote"][0], 70.0)
        self.assertEqual(d["temp_zone"]["interna"][3], 90.0)
        z0 = bytearray(512)
        self.assertNotIn("temp_zone", decodifica_physics(bytes(z0)))
        r = RegistroStile(os.path.join(tempfile.mkdtemp(), "s.json"))
        def c(giri, i, blocco=False):
            return {"collegato": True, "auto": "a", "pista": "p", "giri_completati": giri, "velocita": 120,
                    "freno": 0.9 if i % 4 == 0 else 0.0, "acceleratore": 0.5, "sterzo": 0.0,
                    "vel_ruote": [80, 30, 80, 80] if blocco and i == 4 else [80] * 4,
                    "ultimo_giro_ms": 90000 + giri * 100}
        for giro in range(3):
            for i in range(300):
                r.alimenta(c(giro, i, blocco=(giro == 1)))
        r.alimenta(c(3, 0))
        rep = crea_report(r.giri)
        self.assertEqual(rep["giri"], 3)
        self.assertEqual(rep["blocchi_totali"], 1)
        self.assertEqual(rep["blocchi_per_ruota"], {"ant_dx": 1})
        self.assertTrue(any("bloccato" in n for n in rep["note"]))
        self.assertIsNone(crea_report([]))


class TestSessioni(unittest.TestCase):
    def test_elenco_e_dettaglio(self):
        from simapex.report import elenco_sessioni, dettaglio_sessione
        base = 1000000
        g = lambda n, ts, a="a", t=90000: {"auto": a, "pista": "p", "tempo_ms": t, "ts": ts, "giro": n, "blocchi": [],
                                           "carburante": 50 - n, "gomme": {"p": [27.0] * 4, "t": [80] * 4, "z": [[90] * 4, [80] * 4, [70] * 4]}}
        giri = [g(1, base), g(2, base + 100, t=91000), g(1, base + 5000), g(2, base + 5100)]
        el = elenco_sessioni(giri)
        self.assertEqual(len(el), 2)
        self.assertEqual(el[0]["id"], base + 5000)
        d = dettaglio_sessione(giri, base)
        self.assertEqual(d["giri"], 2)
        self.assertEqual(d["carburante_inizio"], 49)
        self.assertEqual(d["gomme"]["temperatura_zone_C"]["ant_sx"]["interna"], 90)
        self.assertTrue(any("interno" in n for n in d["note"]))
        self.assertIsNone(dettaglio_sessione(giri, 5))

    def test_stile_salva_gomme_e_carburante(self):
        from simapex.stile import RegistroStile
        r = RegistroStile(os.path.join(tempfile.mkdtemp(), "s.json"))
        c = lambda giri: {"collegato": True, "auto": "a", "pista": "p", "giri_completati": giri, "velocita": 120,
                          "freno": 0.0, "acceleratore": 0.5, "sterzo": 0.0, "carburante": 40.0,
                          "pressioni": [27.0] * 4, "temp_gomme": [80.0] * 4, "ultimo_giro_ms": 90000}
        for _ in range(300):
            r.alimenta(c(0))
        r.alimenta(c(1))
        self.assertEqual(r.giri[0]["carburante"], 40.0)
        self.assertEqual(r.giri[0]["gomme"]["t"], [80] * 4)


class TestCircuito(unittest.TestCase):
    def test_registra_giro_e_ricarica(self):
        import math
        from simapex.circuito import Registratore, carica_tracciato
        cart = tempfile.mkdtemp()
        creati = []
        r = Registratore(cart, lambda p, t: creati.append(p))
        def d(giri, i):
            a = 2 * math.pi * i / 600
            return {"collegato": True, "pista": "monza", "giri_completati": giri, "pos_norm": i / 600.0,
                    "coordinate": [500 * math.cos(a), 0, 300 * math.sin(a)], "velocita": 100 + i % 50}
        for i in range(600):
            r.alimenta(d(0, i))
        for i in range(600):
            r.alimenta(d(1, i))
        r.alimenta(d(2, 0))
        t = carica_tracciato("monza", cart)
        self.assertIsNotNone(t)
        self.assertEqual(len(t["x"]), 400)
        self.assertEqual(creati, ["monza"])
        self.assertIsNone(carica_tracciato("altra", cart))

    def test_dati_non_validi_scartati(self):
        from simapex.circuito import costruisci
        self.assertIsNone(costruisci([(i / 500.0, 0.0, 0.0, 50) for i in range(500)]))

    def test_decodifica_graphics_coordinate(self):
        import struct
        from simapex.telemetria import decodifica_graphics
        b = bytearray(1280)
        struct.pack_into("<f", b, 248, 0.25)
        struct.pack_into("<i", b, 1216, 7)
        struct.pack_into("<60i", b, 976, *([0, 7] + [0] * 58))
        struct.pack_into("<3f", b, 256 + 12, 10.0, 2.0, -30.0)
        g = decodifica_graphics(bytes(b))
        self.assertEqual(g["coordinate"], [10.0, 2.0, -30.0])
        self.assertEqual(g["pos_norm"], 0.25)


class TestRispostaTagliata(unittest.TestCase):
    def test_recupera_modifiche_complete(self):
        from simapex.assistente import estrai_json
        testo = '{"problema":"p","spiegazione":"s","cosa_aspettarsi":"c","modifiche":[{"percorso":"a","click":1,"motivo":"m"},{"percorso":"b","click":-2,"motivo":"n"},{"percorso":"c","cl'
        r = estrai_json(testo)
        self.assertEqual(len(r["modifiche"]), 2)
        self.assertEqual(r["problema"], "p")
        with self.assertRaises(ValueError):
            estrai_json("{rotto")


class TestEsito(unittest.TestCase):
    def test_meglio_peggio_uguale(self):
        from simapex.esito import valuta, aggiorna
        def giro(ts, t, bl=0):
            return {"auto": "a", "pista": "p", "tempo_ms": t, "ts": ts, "blocchi": [{}] * bl}
        prima = [giro(100 + i, 92000 + (i % 3) * 100) for i in range(6)]
        voce = {"id": 1000, "auto": "a", "pista": "p"}
        meglio = [giro(1100 + i, 91400 + (i % 3) * 100) for i in range(6)]
        peggio = [giro(1100 + i, 92700 + (i % 3) * 100) for i in range(6)]
        uguale = [giro(1100 + i, 92000 + (i % 3) * 100) for i in range(6)]
        self.assertEqual(valuta(prima + meglio, voce)["esito"], "meglio")
        self.assertEqual(valuta(prima + peggio, voce)["esito"], "peggio")
        self.assertEqual(valuta(prima + uguale, voce)["esito"], "uguale")
        self.assertIsNone(valuta(prima + meglio[:2], voce))
        q = [dict(voce, esito=None)]
        self.assertTrue(aggiorna(q, prima + meglio))
        self.assertEqual(q[0]["esito"], "meglio")
        q[0]["esito_auto"] = False
        q[0]["esito"] = "peggio"
        aggiorna(q, prima + meglio)
        self.assertEqual(q[0]["esito"], "peggio")  # la scelta a mano non si tocca


class TestTracce(unittest.TestCase):
    def _giro(self, rallenta=False):
        camp, pos, t = [], 0.0, 0.0
        while pos < 1:
            v = 150 - (40 if rallenta and 0.3 < pos < 0.4 else 0)
            camp.append((pos, t * 1000, v, 0.0, 0.5))
            pos += v / 150.0 / 750.0
            t += 0.02
        return camp, int(t * 1000)

    def test_costruisci_confronta_e_delta(self):
        from simapex import tracce as tr
        c1, t1 = self._giro()
        c2, t2 = self._giro(rallenta=True)
        a, b = tr.costruisci(c1, t1, t1), tr.costruisci(c2, t2, t2)
        self.assertEqual(len(a["t"]), tr.N + 1)
        self.assertGreater(t2, t1)
        seg = tr.confronta(b, a)           # b (lento) rispetto ad a: perde nei tratti 6-7
        self.assertGreater(sum(seg), 0)
        perd = tr.tratti_principali(seg)[1]
        self.assertTrue(set(perd) & {6, 7})
        self.assertIsNone(tr.costruisci(c1[:50], t1, t1))

    def test_registra_e_delta_live(self):
        import time as _t
        from simapex.tracce import Tracce
        tr = Tracce(tempfile.mkdtemp())
        base = {"collegato": True, "auto": "a", "pista": "p", "in_box": False, "velocita": 100, "freno": 0, "acceleratore": 1}
        # giro simulato in fretta: forzo il tempo del giro
        tr._azzera(dict(base, giri_completati=0))
        for i in range(400):
            tr.t0 = _t.time() - i * 0.05
            tr.alimenta(dict(base, giri_completati=0, pos_norm=i / 400.0))
        tr.alimenta(dict(base, giri_completati=1, pos_norm=0.0, ultimo_giro_ms=20000))
        self.assertIsNotNone(tr.carica("a", "p")["migliore"])
        self.assertEqual(tr.carica("a", "p")["migliore"]["tempo_ms"], 20000)
        self.assertIsNone(tr.delta_live(dict(base, pos_norm=0.0)))


if __name__ == "__main__":
    unittest.main()
