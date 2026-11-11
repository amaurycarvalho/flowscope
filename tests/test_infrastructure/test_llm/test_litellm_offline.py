"""Testes do preparo offline do catálogo de model cost map do liteLLM."""

import builtins
import os
import subprocess
import sys
import textwrap
import types

import pytest

from flowscope.infrastructure.llm import (
    VARIAVEL_MODEL_COST_MAP_LOCAL,
    adapter as adapter_module,
    preparar_litellm,
    presets as presets_module,
)

pytestmark = pytest.mark.llm


class TestPrepararLitellm:
    def test_define_variavel_quando_ausente(self, monkeypatch):
        monkeypatch.delenv(VARIAVEL_MODEL_COST_MAP_LOCAL, raising=False)

        preparar_litellm()

        assert os.environ[VARIAVEL_MODEL_COST_MAP_LOCAL] == "True"

    def test_preserva_valor_ja_definido(self, monkeypatch):
        monkeypatch.setenv(VARIAVEL_MODEL_COST_MAP_LOCAL, "True")

        preparar_litellm()

        assert os.environ[VARIAVEL_MODEL_COST_MAP_LOCAL] == "True"

    def test_override_false_nao_e_sobrescrito(self, monkeypatch):
        monkeypatch.setenv(VARIAVEL_MODEL_COST_MAP_LOCAL, "False")

        preparar_litellm()

        assert os.environ[VARIAVEL_MODEL_COST_MAP_LOCAL] == "False"


class TestImportChamaPreparo:
    @pytest.mark.parametrize(
        "module",
        [presets_module, adapter_module],
        ids=["presets", "adapter"],
    )
    def test_helper_e_chamado_antes_do_import(self, monkeypatch, module):
        ordem: list[str] = []
        monkeypatch.setattr(
            module, "preparar_litellm", lambda: ordem.append("helper")
        )
        falso = types.ModuleType("litellm")
        falso.suppress_debug_info = False
        real_import = builtins.__import__

        def import_falso(name, *args, **kwargs):
            if name == "litellm":
                ordem.append("import")
                return falso
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", import_falso)

        module._import_litellm()

        assert ordem == ["helper", "import"]
        assert falso.suppress_debug_info is True


def test_import_usa_catalogo_local_sem_busca_remota():
    script = textwrap.dedent(
        """
        import os

        os.environ.pop("LITELLM_LOCAL_MODEL_COST_MAP", None)

        from flowscope.infrastructure.llm import adapter

        adapter._import_litellm()

        from litellm.litellm_core_utils.get_model_cost_map import (
            get_model_cost_map_source_info,
        )

        info = get_model_cost_map_source_info()
        assert info["source"] == "local", info
        assert info["is_env_forced"] is True, info
        print("OK")
        """
    )
    ambiente = {
        chave: valor
        for chave, valor in os.environ.items()
        if chave != VARIAVEL_MODEL_COST_MAP_LOCAL
    }

    resultado = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        env=ambiente,
        timeout=120,
    )

    assert resultado.returncode == 0, resultado.stderr
    assert "OK" in resultado.stdout
    assert "model cost map fetch attempt" not in resultado.stderr
    assert "Failed to fetch remote model cost map" not in resultado.stderr
    assert "Falling back to local backup" not in resultado.stderr
