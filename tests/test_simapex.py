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
            server.PORTA = 8765
            server._fermati.clear()
            server.salva_impostazioni({"claude_key": "sk-ant-x"})
            t = threading.Thread(target=server.main, kwargs={"apri_browser": False}, daemon=True)
            t.start()
            for _ in range(40):
                try:
                    urllib.request.urlopen("http://127.0.0.1:8765/api/stato", timeout=1)
                    break
                except Exception:
                    time.sleep(0.25)
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


class TestMulti(unittest.TestCase):
    def test_acc_spento_non_copre_f1(self):
        from simapex import f1 as _f1
        class A:
            def __init__(s, c): s.c = c
            def stato(s): return {"collegato": True, "stato_codice": s.c}
        class F:
            def stato(s): return {"collegato": True, "gioco": "F1 25"}
        self.assertEqual(_f1.LettoreMulti(A(0), F()).stato()["gioco"], "F1 25")
        self.assertEqual(_f1.LettoreMulti(A(2), F()).stato()["gioco"], "ACC")


class TestTastiVolante(unittest.TestCase):
    def test_assegna_e_conta(self):
        from simapex import ptt
        seq = [set(), {7}, set(), {7}, set(), {30}, set(), {30}, set()]
        it = iter(seq)
        p = ptt.Ptt(0, pulsanti=lambda: next(it), azioni={"avanti": 30})
        p.assegna = "ripeti"
        for _ in range(4):
            p.passo()
        self.assertEqual(p.azioni["ripeti"], 7)
        self.assertEqual(p.conta["ripeti"], 1)
        for _ in range(5):
            p.passo()
        self.assertEqual(p.conta["avanti"], 2)


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



class TestMappe(unittest.TestCase):
    RISP = json.dumps({"auto": "Ferrari 296 GT3", "mappe": [{"numero": 1, "cosa_fa": "piena potenza"}, {"numero": 2, "cosa_fa": "meno potenza"}, {"numero": 99, "cosa_fa": "x"}],
                       "mappa_giri_costanti": 2, "mappa_spinta": 1, "quando_spingere": "in qualifica", "quando_passo_costante": "in gara",
                       "come_si_cambia": "tasto", "affidabilita": "alta", "nota": ""})

    def test_cerca_salva_e_rilegge(self):
        import tempfile
        from simapex import mappe
        d = tempfile.mkdtemp()
        chiamate = []

        def finto(k, dom, **kw):
            chiamate.append(kw.get("strumenti"))
            return self.RISP, {"fonti": ["https://esempio.it/a"]}
        r = mappe.cerca("k", d, "ferrari_296_gt3", chiedi=finto)
        self.assertEqual([m["numero"] for m in r["mappe"]], [1, 2])
        self.assertTrue(r["ricerca_online"])
        self.assertEqual(mappe.leggi(d, "ferrari_296_gt3")["mappa_giri_costanti"], 2)
        self.assertIsNone(mappe.leggi(d, "altra_auto"))

    def test_senza_ricerca_web_riprova(self):
        import tempfile
        from simapex import mappe
        d = tempfile.mkdtemp()

        def finto(k, dom, **kw):
            if kw.get("strumenti"):
                raise RuntimeError("richiesta rifiutata (web search non abilitata).")
            return self.RISP, {"fonti": []}
        r = mappe.cerca("k", d, "ferrari_296_gt3", chiedi=finto)
        self.assertFalse(r["ricerca_online"])
        self.assertEqual(r["affidabilita"], "media")


class TestPressioniESessioni(unittest.TestCase):
    def _giro(self, n, p, sess=0, ts=1000, pos=None, tempo=100000):
        return {"auto": "a", "pista": "p", "giro": n, "tempo_ms": tempo + n * 10, "ts": ts + n * 100, "sess": sess, "pos": pos,
                "carburante": 40 - n * 2.0, "blocchi": [], "gomme": {"p": p, "t": [80] * 4}}

    def test_pressioni_alte_servono_click_negativi(self):
        from simapex import pressioni
        giri = [self._giro(i, [27.6, 27.6, 26.7, 26.0]) for i in range(1, 8)]
        r = pressioni.proposta(giri, None)
        click = {m["percorso"]: m["click"] for m in r["modifiche"]}
        self.assertEqual(click["basicSetup.tyres.tyrePressure[0]"], -9)
        self.assertNotIn("basicSetup.tyres.tyrePressure[2]", click)  # già nell'intervallo
        self.assertEqual(click["basicSetup.tyres.tyrePressure[3]"], 7)

    def test_pochi_giri_nessuna_modifica(self):
        from simapex import pressioni
        r = pressioni.proposta([self._giro(i, [27.5] * 4) for i in range(1, 4)], None)
        self.assertEqual(r["modifiche"], [])

    def test_sessioni_divise_per_tipo_e_report_gara(self):
        from simapex import report
        giri = [self._giro(i, [26.7] * 4, sess=0, ts=1000) for i in range(1, 4)]
        giri += [self._giro(i, [26.7] * 4, sess=2, ts=1500, pos=5 - i // 3) for i in range(1, 8)]
        sess = report.tutte_le_sessioni(giri)
        self.assertEqual([report.tipo_sessione(s) for s in reversed(sess)], ["prove libere", "gara"])
        det = report.crea_report(giri, sessione=sess[0])
        self.assertEqual(det["tipo"], "gara")
        self.assertTrue(any(n.startswith("Gara:") for n in det["note"]))

    def test_stile_registra_giri_dopo_nuova_sessione(self):
        import tempfile
        from simapex.stile import RegistroStile
        reg = RegistroStile(os.path.join(tempfile.mkdtemp(), "stile.json"))

        def d(gc, sess, ultimo=0):
            return {"collegato": True, "auto": "a", "pista": "p", "giri_completati": gc, "sessione": sess, "velocita": 120.0,
                    "freno": 0.0, "acceleratore": 0.5, "sterzo": 0.1, "ultimo_giro_ms": ultimo, "posizione": 3, "carburante": 30.0}
        for gc in range(0, 3):          # prove: 3 giri
            for _ in range(250):
                reg.alimenta(d(gc, 0))
        reg.alimenta(d(3, 0, 100000))
        n0 = len(reg.giri)
        for _ in range(5):
            reg.alimenta(d(0, 2))       # nuova sessione: i giri ripartono da 0
        for gc in range(0, 2):
            for _ in range(250):
                reg.alimenta(d(gc, 2))
        reg.alimenta(d(2, 2, 99000))
        self.assertEqual(len(reg.giri), n0 + 1)
        self.assertEqual(reg.giri[-1]["sess"], 2)


class TestF1(unittest.TestCase):
    def _int(self, pid, player=3):
        # formato 2025, anno 25, versione 1.0, pacchetto pid, 22 auto
        return struct.pack("<HBBBBBQfIIBB", 2025, 25, 1, 0, 1, pid, 1, 12.5, 100, 100, player, 255)

    def _tele(self, player=3):
        corpo = bytearray(60 * 22 + 3)
        o = player * 60
        struct.pack_into("<Hfff", corpo, o, 180, 0.8, -0.2, 0.0)
        struct.pack_into("<bH", corpo, o + 15, 4, 9000)
        struct.pack_into("<4H", corpo, o + 22, 400, 410, 300, 310)             # RL RR FL FR
        struct.pack_into("<4B", corpo, o + 34, 90, 91, 80, 81)
        struct.pack_into("<4f", corpo, o + 40, 22.0, 22.1, 23.0, 23.1)
        return self._int(6, player) + bytes(corpo)

    def test_telemetria_e_ordine_ruote(self):
        from simapex import f1
        r = f1.LettoreF1()
        r.elabora(self._tele())
        s = r.d
        self.assertEqual(s["marcia"], "4")
        self.assertEqual(s["velocita"], 180.0)
        self.assertEqual(s["pressioni"], [23.0, 23.1, 22.0, 22.1])      # ordine ACC: ant sx, ant dx, post sx, post dx
        self.assertEqual(s["temp_gomme"], [80.0, 81.0, 90.0, 91.0])
        self.assertEqual(len(self._tele()), 1352)

    def test_giri_sessione_pista(self):
        from simapex import f1
        r = f1.LettoreF1()
        sess = bytearray(753 - 29)
        struct.pack_into("<BbbB", sess, 0, 0, 30, 24, 5)
        struct.pack_into("<HBb", sess, 4, 7004, 15, 10)    # lunghezza, gara, Spa
        r.elabora(self._int(1) + bytes(sess))
        corpo = bytearray(57 * 22 + 2)
        o = 3 * 57
        struct.pack_into("<II", corpo, o, 0, 30000)
        struct.pack_into("<f", corpo, o + 20, 3502.0)
        struct.pack_into("<6B", corpo, o + 32, 4, 2, 0, 0, 1, 0)
        r.elabora(self._int(2) + bytes(corpo))
        r.elabora(self._tele())
        s = r.stato()
        self.assertTrue(s["collegato"])
        self.assertEqual(s["gioco"], "F1 25")
        self.assertEqual(s["pista"], "spa")
        self.assertEqual(s["sessione"], 2)
        self.assertEqual(s["giri_completati"], 1)
        self.assertAlmostEqual(s["pos_norm"], 0.5, places=2)
        self.assertEqual(s["posizione"], 4)
        # giro completato valido: il migliore si aggiorna
        corpo2 = bytearray(corpo)
        struct.pack_into("<II", corpo2, o, 98765, 1000)
        struct.pack_into("<6B", corpo2, o + 32, 4, 3, 0, 0, 0, 0)
        r.elabora(self._int(2) + bytes(corpo2))
        self.assertEqual(r.stato()["miglior_giro_ms"], 98765)

    def test_lunghezza_inattesa_scartata(self):
        from simapex import f1
        r = f1.LettoreF1()
        r.elabora(self._int(6) + bytes(100))
        self.assertIn(6, r.scartati)
        self.assertNotIn("velocita", r.d)

    def test_ruote_in_rad_s_per_i_blocchi(self):
        from simapex import f1, stile
        r = f1.LettoreF1()
        corpo = bytearray(273 - 29)
        struct.pack_into("<4f", corpo, 48, 20.0, 20.0, 8.0, 20.0)       # RL RR FL FR: ant sx bloccata
        r.elabora(self._int(13) + bytes(corpo))
        d = {"vel_ruote": r.d["vel_ruote"], "freno": 0.9, "velocita": 200}
        self.assertEqual(stile.ruota_bloccata(d), 0)

    def test_f1_extra_stato_sessione_danni(self):
        from simapex import f1
        r = f1.LettoreF1()
        sess = bytearray(753 - 29)
        struct.pack_into("<BbbB", sess, 0, 0, 30, 24, 12)
        struct.pack_into("<HBb", sess, 4, 7004, 15, 10)
        struct.pack_into("<H", sess, 9, 1800)
        sess[124] = 2
        r.elabora(self._int(1) + bytes(sess))
        st = bytearray(55 * 22)
        o = 3 * 55
        struct.pack_into("<f", st, o + 5, 40.5)
        struct.pack_into("<f", st, o + 13, 11.2)
        st[o + 26], st[o + 27] = 17, 5
        struct.pack_into("<f", st, o + 37, 2000000.0)
        r.elabora(self._int(7) + bytes(st))
        dn = bytearray(46 * 22)
        struct.pack_into("<4f", dn, 3 * 46, 10.0, 11.0, 20.0, 21.0)       # RL RR FL FR
        r.elabora(self._int(10) + bytes(dn))
        r.elabora(self._tele())
        s = r.stato()
        self.assertEqual(s["giri_totali"], 12)
        self.assertEqual(s["tempo_rimasto_s"], 1800)
        self.assertEqual(s["safety_car"], "safety car virtuale")
        self.assertEqual(s["usura_gomme"], [20.0, 21.0, 10.0, 11.0])
        self.assertEqual(s["mescola"], "media")
        self.assertEqual(s["eta_gomme"], 5)
        self.assertEqual(s["giri_carburante_gioco"], 11.2)
        self.assertEqual(s["ers_pct"], 50)

    def test_ingegnere_contesto(self):
        from simapex import ingegnere
        c = ingegnere.contesto({"gioco": "F1 25", "sessione": 2, "carburante": 12.5, "pressioni": [22, 22, 23, 23]})
        self.assertIn("gara", c)
        self.assertIn("Carburante: 12.5", c)
        self.assertIn("nessun dato", ingegnere.contesto({}).lower())
        with self.assertRaises(RuntimeError):
            ingegnere.rispondi("k", "  ", {})

    def test_f1_distacchi(self):
        from simapex import f1
        r = f1.LettoreF1()
        corpo = bytearray(57 * 22 + 2)
        def metti(i, pos, ultimo, delta):
            o = i * 57
            struct.pack_into("<I", corpo, o, ultimo)
            struct.pack_into("<HB", corpo, o + 14, delta % 60000, delta // 60000)
            corpo[o + 32] = pos
        metti(2, 3, 91000, 1500)   # davanti (posizione 3)
        metti(3, 4, 92000, 2200)   # io (posizione 4)
        metti(4, 5, 93000, 900)    # dietro (posizione 5)
        r.elabora(self._int(2) + bytes(corpo))
        r.elabora(self._tele())
        s = r.stato()
        self.assertEqual(s["distacco_davanti_ms"], 2200)
        self.assertEqual(s["distacco_dietro_ms"], 900)
        self.assertEqual(s["ultimo_davanti_ms"], 91000)
        self.assertEqual(s["ultimo_dietro_ms"], 93000)

    def test_vicini_acc(self):
        from simapex.telemetria import calcola_vicini
        v = calcola_vicini([0, 0, 0], [0, 20], [[3, 0], [-3, 2], [0, -10], [100, 0]])
        self.assertEqual(v[0], {"lon": 0.0, "lat": 3.0})
        self.assertEqual(calcola_vicini([0, 0, 0], [0, 1], [[3, 0]]), [])

    def test_f1_setup_letto(self):
        from simapex import f1
        r = f1.LettoreF1()
        corpo = bytearray(50 * 22 + 4)
        o = 3 * 50
        corpo[o:o + 4] = bytes([8, 6, 70, 60])
        struct.pack_into("<4f", corpo, o + 4, -3.0, -1.5, 0.05, 0.2)
        corpo[o + 20:o + 29] = bytes([5, 3, 6, 4, 20, 30, 95, 58, 50])
        struct.pack_into("<4f", corpo, o + 29, 21.0, 21.1, 23.0, 23.1)   # RL RR FL FR
        corpo[o + 45] = 7
        struct.pack_into("<f", corpo, o + 46, 38.0)
        r.elabora(self._int(5) + bytes(corpo))
        r.elabora(self._tele())
        st = r.stato()["setup_f1"]
        self.assertEqual(st["ala anteriore"], 8)
        self.assertEqual(st["ripartizione freni % anteriore"], 58)
        self.assertEqual(st["pressioni gomme psi (AS, AD, PS, PD)"], [23.0, 23.1, 21.0, 21.1])
        self.assertEqual(st["carburante a inizio sessione"], 38.0)

    def test_ptt_e_confronto_giri(self):
        from simapex import ptt, tracce
        p = ptt.Ptt(25, pulsanti=lambda: {3, 25})
        p.passo()
        self.assertTrue(p.premuto)
        self.assertEqual(p.ultimi, [3, 25])
        p.tasto = 9
        p.passo()
        self.assertFalse(p.premuto)
        t = [i * 500 for i in range(201)]
        t2 = [i * 510 for i in range(201)]
        g1 = {"tempo_ms": t[-1], "t": t, "v": [100] * 200, "f": [0] * 200, "g": [0] * 200, "ts": 10}
        g2 = {"tempo_ms": t2[-1], "t": t2, "v": [100] * 200, "f": [0] * 200, "g": [0] * 200, "ts": 20}
        class T:
            def carica(self, a, b):
                return {"giri": [g1, g2], "migliore": g1}
        c = tracce.confronto_giri(T(), "a", "b", tracce.chiave_giro(g1), tracce.chiave_giro(g2))
        seg = c["rif"]["scelto"]["segmenti"]
        self.assertEqual(len(seg), 25)
        self.assertTrue(all(x < 0 for x in seg))
        self.assertEqual(len(tracce.lista_giri(T(), "a", "b")), 2)

    def test_setup_f1_assistente(self):
        from simapex import assistente_f1, esito
        setup = {"ala anteriore": 8, "ala posteriore": 6, "campanatura anteriore": -3.0, "carburante a inizio sessione": 38.0,
                 "pressioni gomme psi (AS, AD, PS, PD)": [23.0, 23.1, 21.0, 21.1]}
        ok, scart = assistente_f1.valida(setup, [
            {"parametro": "ala posteriore", "a": 9, "motivo": "più carico dietro"},
            {"parametro": "ala anteriore", "a": 40, "motivo": "troppo"},
            {"parametro": "carburante a inizio sessione", "a": 30, "motivo": "no"},
            {"parametro": "inventato", "a": 3, "motivo": "no"},
            {"parametro": "campanatura anteriore", "a": -3.2, "motivo": "ok"}])
        self.assertEqual([m["parametro"] for m in ok], ["ala posteriore", "campanatura anteriore"])
        self.assertEqual(scart, 3)
        voce = {"modifiche": ok}
        self.assertFalse(assistente_f1.applicato(voce, setup))
        self.assertTrue(assistente_f1.applicato(voce, {"ala posteriore": 9, "campanatura anteriore": -3.2}))
        # l'esito parte dal momento in cui il pilota ha messo il setup nel gioco
        giri = [{"auto": "a", "pista": "p", "ts": 100 + i, "tempo_ms": 90000 + (i % 3) * 100} for i in range(5)] + \
               [{"auto": "a", "pista": "p", "ts": 300 + i, "tempo_ms": 89000 + (i % 3) * 100} for i in range(5)]
        v = {"id": 150, "auto": "a", "pista": "p", "f1": True, "modifiche": ok}
        self.assertEqual(esito.aggiorna([v], giri), False)       # non ancora applicato
        v["ts_applicato"] = 250
        self.assertTrue(esito.aggiorna([v], giri))
        self.assertEqual(v["esito"], "meglio")

    def _giro(self, tempo, ts, rapido_seg=None):
        from simapex import tracce
        N, per = tracce.N, tracce.N // tracce.SEGMENTI
        t = [0.0]
        for i in range(N):
            dur = tempo / N
            if rapido_seg is not None and i // per == rapido_seg:
                dur *= 0.9
            t.append(t[-1] + dur)
        return {"tempo_ms": round(t[-1]), "t": [round(x) for x in t], "v": [100 + (i // per) for i in range(N)],
                "f": [0.1] * N, "g": [0.5] * N, "ts": ts}

    def test_riferimenti_e_consiglio(self):
        from simapex import tracce
        giri = [self._giro(90000, 10 + i, rapido_seg=i % 5) for i in range(6)]
        class T:
            def carica(self, a, b):
                return {"giri": giri, "migliore": min(giri, key=lambda g: g["tempo_ms"])}
        r = tracce.riferimenti(T(), "a", "p")
        self.assertEqual(set(r), {"@record", "@passo", "@ideale", "@teorico"})
        self.assertLess(r["@teorico"]["tempo_ms"], min(g["tempo_ms"] for g in giri))
        self.assertLessEqual(r["@teorico"]["tempo_ms"], r["@ideale"]["tempo_ms"])
        self.assertEqual(len(r["@teorico"]["t"]), tracce.N + 1)
        c = tracce.confronto_giri(T(), "a", "p", tracce.chiave_giro(giri[5]), "@teorico")
        self.assertEqual(len(c["rif"]["scelto"]["f"]), tracce.N)
        lento = self._giro(92000, 99)
        lento["f"] = [0.8] * tracce.N
        cons = tracce.consiglio_giro(lento, giri[0])
        self.assertIn("Microsettore", cons["testo"])

    def test_box_corsia_e_perdita(self):
        import tempfile
        from simapex import circuito
        cart = tempfile.mkdtemp()
        b = circuito.Box(cart)
        base = {"collegato": True, "pista": "spa", "auto": "x"}
        t0 = 1000.0
        b.alimenta(dict(base, in_box=False, pos_norm=0.95), ora=t0)
        for k in range(40):
            b.alimenta(dict(base, in_box=True, pos_norm=0.97, coordinate=[k, 0, k * 2], velocita=60 if k < 15 or k > 30 else 0), ora=t0 + 1 + k)
        b.alimenta(dict(base, in_box=False, pos_norm=0.03), ora=t0 + 45)
        box = circuito.carica_box(cart, "spa")
        self.assertEqual(box["entra"], 0.95)
        self.assertEqual(len(box["soste"]), 1)
        self.assertGreater(box["soste"][0]["fermo_ms"], 10000)
        tr = {"t": [round(i * 450) for i in range(201)]}   # giro da 90 s
        i = circuito.info_box(cart, "spa", "x", tr)
        self.assertGreater(i["perdita_ms"], 0)
        self.assertEqual(i["perdita_con_sosta_ms"], i["perdita_ms"] + i["fermo_ms"])

    def test_salto_a_fine_giro_non_sporca(self):
        from simapex import circuito
        r = circuito.Registratore("/nonexistent/x")
        base = {"collegato": True, "pista": "p", "giri_completati": 1, "coordinate": [0, 0, 0], "velocita": 100}
        r.alimenta(dict(base, pos_norm=0.5, coordinate=[0, 0, 0]))
        r.alimenta(dict(base, pos_norm=0.6, coordinate=[1, 0, 1]))
        r.alimenta(dict(base, pos_norm=0.99, coordinate=[2, 0, 2]))
        r.alimenta(dict(base, pos_norm=0.01, coordinate=[3, 0, 3]))   # la posizione riparte prima del contatore dei giri
        self.assertFalse(r.sporco)
        r.alimenta(dict(base, pos_norm=0.5, coordinate=[3, 0, 3]))
        r.alimenta(dict(base, pos_norm=0.1, coordinate=[3, 0, 3]))    # salto vero a metà giro
        self.assertTrue(r.sporco)


if __name__ == "__main__":
    unittest.main()
