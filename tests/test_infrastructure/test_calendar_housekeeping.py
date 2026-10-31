import json

from flowscope.infrastructure.calendar.housekeeping import (
    is_retained,
    run_housekeeping,
)


def _write(path, year, payload=None):
    path.mkdir(parents=True, exist_ok=True)
    (path / f"{year}.json").write_text(
        json.dumps(payload if payload is not None else {"year": year}),
        encoding="utf-8",
    )


def test_janela_de_retencao():
    assert is_retained(2023, 2026)
    assert is_retained(2027, 2026)
    assert not is_retained(2022, 2026)
    assert not is_retained(2028, 2026)


def test_remove_anos_fora_da_janela(tmp_path):
    for year in (2021, 2023, 2024, 2025, 2026, 2027):
        _write(tmp_path, year)
    removidos = run_housekeeping(tmp_path, 2026)
    assert removidos == [2021]
    assert sorted(path.stem for path in tmp_path.glob("*.json")) == [
        "2023", "2024", "2025", "2026", "2027",
    ]


def test_protege_ano_da_operacao(tmp_path):
    _write(tmp_path, 2021)
    removidos = run_housekeeping(tmp_path, 2026, protected_years=(2021,))
    assert removidos == []
    assert (tmp_path / "2021.json").exists()


def test_corrompido_e_ignorado(tmp_path):
    (tmp_path / "2020.json").write_text("{invalido", encoding="utf-8")
    removidos = run_housekeeping(tmp_path, 2026)
    assert removidos == []
    assert (tmp_path / "2020.json").exists()


def test_diretorio_ausente_nao_falha(tmp_path):
    assert run_housekeeping(tmp_path / "ausente", 2026) == []
