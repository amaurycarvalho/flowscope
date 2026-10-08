import json
import types
from unittest.mock import patch

import pytest

from flowscope.presentation.gui.app import (
    FlowScopeGUI,
    load_preferences,
    save_preferences,
)
from flowscope.presentation.gui.app_tab_layout import (
    MIN_PAINEL_DIREITO,
    MIN_PAINEL_ESQUERDO,
    TabsLayoutMixin,
)


def _carregar_sash(tmp_path, valor):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"sash_positions": valor}), encoding="utf-8")
    with patch("flowscope.presentation.gui.app.CONFIG_DIR", tmp_path), patch(
        "flowscope.presentation.gui.app.CONFIG_PATH", path
    ):
        return load_preferences()["sash_positions"]


class TestSashPositionsPreferences:
    def test_largura_valida_preservada(self, tmp_path):
        assert _carregar_sash(tmp_path, 320) == 320

    def test_round_trip_largura(self, tmp_path):
        with patch("flowscope.presentation.gui.app.CONFIG_DIR", tmp_path), patch(
            "flowscope.presentation.gui.app.CONFIG_PATH", tmp_path / "config.json"
        ):
            save_preferences({"sash_positions": 280})
            assert load_preferences()["sash_positions"] == 280

    def test_formato_legado_descartado(self, tmp_path):
        assert _carregar_sash(tmp_path, [856, 1, 1, 554]) is None

    def test_missing_key_returns_none(self, tmp_path):
        with patch("flowscope.presentation.gui.app.CONFIG_DIR", tmp_path), patch(
            "flowscope.presentation.gui.app.CONFIG_PATH", tmp_path / "config.json"
        ):
            assert load_preferences()["sash_positions"] is None

    @pytest.mark.parametrize("valor", [0, -10, "300", True, None, [1, 2]])
    def test_valores_invalidos_descartados(self, tmp_path, valor):
        assert _carregar_sash(tmp_path, valor) is None


class _FakePaned:
    """PanedWindow mínimo (sem Tk) que registra ``sash_place``."""

    def __init__(self, total: int) -> None:
        self._total = total
        self.place = None

    def winfo_width(self) -> int:
        return self._total

    def sash_place(self, index: int, x: int, y: int) -> None:
        self.place = (index, x, y)


class _FakePanedCoord:
    """PanedWindow mínimo que devolve largura e coordenada do sash."""

    def __init__(self, total: int, x: int) -> None:
        self._total = total
        self._x = x

    def winfo_width(self) -> int:
        return self._total

    def sash_coord(self, index: int) -> tuple[int, int]:
        return (self._x, 1)


def _host(painel):
    return types.SimpleNamespace(_main_pw=painel)


class TestRestauracaoDivisor:
    def test_largura_aplicada(self):
        pw = _FakePaned(total=1200)
        TabsLayoutMixin._restore_sashes(_host(pw), 300)
        assert pw.place == (0, 900, 0)

    def test_largura_preservada_em_resolucao_maior(self):
        pw1 = _FakePaned(total=1200)
        TabsLayoutMixin._restore_sashes(_host(pw1), 300)
        assert pw1.place is not None
        assert pw1._total - pw1.place[1] == 300

        pw2 = _FakePaned(total=1600)
        TabsLayoutMixin._restore_sashes(_host(pw2), 300)
        assert pw2.place is not None
        assert pw2._total - pw2.place[1] == 300

    def test_clamp_preserva_painel_esquerdo(self):
        pw = _FakePaned(total=600)
        TabsLayoutMixin._restore_sashes(_host(pw), 100000)
        assert pw.place == (0, MIN_PAINEL_ESQUERDO, 0)

    def test_clamp_preserva_painel_direito(self):
        pw = _FakePaned(total=1000)
        TabsLayoutMixin._restore_sashes(_host(pw), 1)
        assert pw.place is not None
        assert pw._total - pw.place[1] >= MIN_PAINEL_DIREITO

    def test_sem_largura_util_nao_posiciona(self):
        pw = _FakePaned(total=1)
        TabsLayoutMixin._restore_sashes(_host(pw), 300)
        assert pw.place is None


class TestLarguraDivisorSalva:
    def test_calcula_largura_direita(self):
        host = _host(_FakePanedCoord(total=1200, x=900))
        assert FlowScopeGUI._largura_divisor_direito(host) == 300

    def test_largura_nula_quando_painel_direito_colapsado(self):
        host = _host(_FakePanedCoord(total=1200, x=1200))
        assert FlowScopeGUI._largura_divisor_direito(host) is None

    def test_largura_nula_sem_painel(self):
        assert FlowScopeGUI._largura_divisor_direito(types.SimpleNamespace()) is None
