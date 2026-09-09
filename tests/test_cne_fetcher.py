from src.hvac import cne_fetcher


def test_parse_chilean_number():
    assert cne_fetcher._parse_chilean_number("1.234,56") == 1234.56
    assert cne_fetcher._parse_chilean_number("1080,38") == 1080.38
    assert cne_fetcher._parse_chilean_number("0") == 0.0
    assert cne_fetcher._parse_chilean_number(None) == 0.0


def test_fetch_precio_cne_no_disponible():
    res = cne_fetcher.fetch_precio_cne("electricidad", 13)
    assert res["status"] == "error"
    assert "no está disponible" in res["mensaje"]


def test_load_dotenv(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# comentario\n"
        "CNE_API_EMAIL=test@example.com\n"
        "CNE_API_PASSWORD='secreto 123'\n"
        "VACIO\n",
        encoding="utf-8",
    )
    values = cne_fetcher._load_dotenv(str(env_file))
    assert values["CNE_API_EMAIL"] == "test@example.com"
    assert values["CNE_API_PASSWORD"] == "secreto 123"
    assert "VACIO" not in values


def test_get_credentials_prioriza_entorno(monkeypatch):
    monkeypatch.setenv("CNE_API_EMAIL", "env@example.com")
    monkeypatch.setenv("CNE_API_PASSWORD", "envpass")
    email, password = cne_fetcher._get_credentials()
    assert email == "env@example.com"
    assert password == "envpass"


def test_fetch_precio_cne_ok(monkeypatch):
    monkeypatch.setattr(cne_fetcher, "_get_token", lambda: ("token", None))
    monkeypatch.setattr(
        cne_fetcher,
        "_fetch_list",
        lambda path, token: [
            {"fecha": "2026-06-01", "region_cod": 13, "tipo_combustible": "kerosene_domestico", "precio_por_litro": "1.080,38"},
            {"fecha": "2026-05-01", "region_cod": 13, "tipo_combustible": "kerosene_domestico", "precio_por_litro": "1.000,00"},
        ],
    )
    res = cne_fetcher.fetch_precio_cne("parafina", 13)
    assert res["status"] == "ok"
    assert res["precio_por_unidad"] == 1080.38
    assert res["fecha_vigencia"] == "2026-06-01"
    assert res["unidad"] == "litro"


def test_fetch_precio_cne_sin_datos(monkeypatch):
    monkeypatch.setattr(cne_fetcher, "_get_token", lambda: ("token", None))
    monkeypatch.setattr(cne_fetcher, "_fetch_list", lambda path, token: [])
    res = cne_fetcher.fetch_precio_cne("parafina", 13)
    assert res["status"] == "error"
    assert "No se encontró precio" in res["mensaje"]


def test_fetch_precio_cne_error_auth(monkeypatch):
    monkeypatch.setattr(cne_fetcher, "_get_token", lambda: (None, "Credenciales CNE no configuradas."))
    res = cne_fetcher.fetch_precio_cne("parafina", 13)
    assert res["status"] == "error"
    assert "no configuradas" in res["mensaje"]


def test_fetch_all_regions(monkeypatch):
    monkeypatch.setattr(cne_fetcher, "_get_token", lambda: ("token", None))
    monkeypatch.setattr(
        cne_fetcher,
        "_fetch_list",
        lambda path, token: [
            {"fecha": "2026-06-01", "region_cod": 13, "tipo_combustible": "kerosene_domestico",
             "precio_por_litro": "1.080,38"},
            {"fecha": "2026-06-01", "region_cod": 13, "tipo_combustible": "kerosene_domestico",
             "precio_por_litro": "1.080,00"},
            {"fecha": "2026-05-01", "region_cod": 5, "tipo_combustible": "kerosene_domestico",
             "precio_por_litro": "1.050,75"},
            {"fecha": "2026-06-01", "region_cod": 5, "tipo_combustible": "gasolina_93_sp",
             "precio_por_litro": "999"},
            {"fecha": "2026-01-01", "region_cod": 1, "tipo_combustible": "kerosene_domestico",
             "precio_por_litro": "0"},
        ],
    )
    res = cne_fetcher.fetch_all_regions("parafina")
    assert res["status"] == "ok"
    assert len(res["data"]) == 2  # region 13 and 5 (region 1 has price 0, filtered)
    region_cods = {r["region_cod"] for r in res["data"]}
    assert region_cods == {5, 13}
