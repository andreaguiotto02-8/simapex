import unittest
from simapex import server


class TestLimite(unittest.TestCase):
    def test_limite_blocca_e_autorizzazione_vale_una_volta(self):
        orig = server.costo_mese
        try:
            server.costo_mese = lambda: {"dollari": 2.5, "limite": server.LIMITE_MESE}
            server._AUTORIZZATE["n"] = 0
            with self.assertRaises(RuntimeError):
                server._controllo_limite()
            server._AUTORIZZATE["n"] = 1
            server._controllo_limite()
            with self.assertRaises(RuntimeError):
                server._controllo_limite()
            server.costo_mese = lambda: {"dollari": 0.5, "limite": server.LIMITE_MESE}
            server._controllo_limite()
        finally:
            server.costo_mese = orig
            server._AUTORIZZATE["n"] = 0


if __name__ == "__main__":
    unittest.main()
