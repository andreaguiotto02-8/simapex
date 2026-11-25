import json
import os

from simapex import comandi


def _dati():
    return {"commandDevices": [{"productName": "Volante", "uICommandButtonList": [
        {"buttonIndex": 2, "powIndex": -1, "powValue": 0, "keyName": "None", "instantActionCode": "Backward", "extendedActionCode": "None", "pinkieInstanceActionCode": "None"}],
        "raceCommandButtonList": [
        {"buttonIndex": 24, "powIndex": -1, "powValue": 0, "keyName": "None", "instantActionCode": "Pause", "extendedActionCode": "None", "pinkieInstanceActionCode": "None"},
        {"buttonIndex": 4, "powIndex": -1, "powValue": 0, "keyName": "None", "instantActionCode": "GearUp", "extendedActionCode": "None", "pinkieInstanceActionCode": "None"}],
        "raceCommandAxisList": [{"axisIndex": 0, "axisCode": "Steer"}]}]}


def test_voci_e_numeri_da_uno():
    v = comandi.voci_da_dati(_dati())
    p = [x for x in v if x["codice"] == "Pause"][0]
    assert p["numero"] == 25 and p["tasto"] == "tasto 25" and p["nome"] == "Pausa"
    assert v[0]["gruppo"] == "Assi"        # gli assi vengono prima


def test_conflitto_col_tasto_radio():
    r = comandi.analizza(_dati(), {"radio": 25, "avanti": 22})
    assert r["conflitti"] == [{"azione": "radio", "tasto": 25, "con": "Pausa"}]
    assert 25 not in r["liberi"] and 22 in r["liberi"]


def test_copia_e_ripristino(tmp_path):
    cart = tmp_path / "Config"
    cart.mkdir()
    (cart / "controls.json").write_text(json.dumps(_dati()), encoding="utf-8")
    dati = str(tmp_path / "dati")
    os.makedirs(dati)
    n = comandi.salva_copia(dati, str(cart))
    assert n and comandi.copie(dati) == [n]
    assert comandi.salva_copia(dati, str(cart)) is None        # niente doppioni se non è cambiato
    (cart / "controls.json").write_text("{}", encoding="utf-8")   # il gioco resetta i comandi
    assert comandi.ripristina(dati, n, True, str(cart))["ok"] is False   # con ACC aperto non si tocca
    assert comandi.ripristina(dati, n, False, str(cart))["ok"] is True
    assert json.loads((cart / "controls.json").read_text(encoding="utf-8")) == _dati()
    assert len(comandi.copie(dati)) == 2                         # copia anche dello stato resettato
