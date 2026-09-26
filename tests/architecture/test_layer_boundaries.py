"""Guarda de fronteira entre as camadas arquiteturais do FlowScope.

Falha quando um import proibido entre camadas é introduzido ou quando a
allowlist contém uma entrada já resolvida. As regras e a varredura vivem em
:mod:`tests.architecture.guardrail`.
"""

from pathlib import Path

import pytest

from tests.architecture import guardrail

_SRC = Path(__file__).resolve().parents[2] / "src" / "flowscope"
_ALLOWLIST = Path(__file__).resolve().parent / "allowlist.txt"


def _violations() -> set[guardrail.Violation]:
    """Retorna as violações de fronteira do código-fonte atual."""
    return guardrail.find_violations(_SRC)


def _allowlist() -> set[guardrail.Violation]:
    """Retorna as entradas da allowlist de violações legadas."""
    return guardrail.read_allowlist(_ALLOWLIST)


class TestFronteirasDeCamada:
    """Verifica o fluxo de dependências e a manutenção da allowlist."""

    def test_sem_violacoes_nao_listadas(self) -> None:
        """Import proibido novo deve reprovar o teste."""
        nao_listadas = guardrail.unlisted_violations(_violations(), _allowlist())
        assert nao_listadas == set(), (
            "Import proibido entre camadas. Mova o código para a camada correta "
            "ou registre a dívida na allowlist: "
            f"{sorted(nao_listadas)}"
        )

    def test_sem_entradas_obsoletas_na_allowlist(self) -> None:
        """Entrada da allowlist sem violação correspondente deve reprovar."""
        obsoletas = guardrail.stale_allowlist_entries(_violations(), _allowlist())
        assert obsoletas == set(), (
            "A allowlist tem entradas sem violação correspondente; remova-as: "
            f"{sorted(obsoletas)}"
        )

    def test_fronteira_zerada(self) -> None:
        """Após o fechamento, não deve restar nenhuma violação nem entrada."""
        assert _violations() == set()
        assert _allowlist() == set()

    def test_allowlist_sem_duplicatas(self) -> None:
        """A allowlist não deve repetir entradas."""
        linhas = [
            linha.split("#", 1)[0].strip()
            for linha in _ALLOWLIST.read_text(encoding="utf-8").splitlines()
        ]
        conteudo = [linha for linha in linhas if linha]
        assert len(conteudo) == len(set(conteudo))

    @pytest.mark.parametrize("origem", guardrail.LAYERS)
    def test_toda_camada_tem_regra(self, origem: str) -> None:
        """Toda camada arquitetural deve ter uma entrada de regras."""
        assert origem in guardrail.FORBIDDEN_IMPORTS

    @pytest.mark.parametrize(
        ("origem", "destino"),
        [
            (origem, destino)
            for origem, destinos in guardrail.FORBIDDEN_IMPORTS.items()
            for destino in sorted(destinos)
        ],
    )
    def test_caso_conhecido_de_cada_regra(self, origem: str, destino: str) -> None:
        """Cada regra deve reconhecer um import sintético da camada proibida."""
        fonte = f"from flowscope.{destino} import algo\n"
        assert destino in guardrail.imported_layers(fonte)
        assert destino in guardrail.FORBIDDEN_IMPORTS[origem]

    def test_import_camada_permitida_nao_e_flagrado(self) -> None:
        """Import de camada não proibida não deve ser detectado como violação."""
        assert guardrail.imported_layers("from flowscope.domain import x\n") == {"domain"}
        assert "domain" not in guardrail.FORBIDDEN_IMPORTS["application"]

    def test_composition_root_isento(self) -> None:
        """Os pontos de composição são exceção estrutural à regra."""
        for caminho in guardrail.COMPOSITION_ROOT:
            assert guardrail.is_exempt(caminho, "presentation", "infrastructure")
        assert not guardrail.is_exempt(
            "presentation/gui/charts/document_tree_panel.py",
            "presentation",
            "infrastructure",
        )


class TestComparacaoAllowlist:
    """Testes sintéticos da comparação allowlist x violações."""

    def test_violacao_nova_reprova(self) -> None:
        """Violação fora da allowlist é reportada."""
        v = ("presentation/novo.py", "infrastructure")
        assert guardrail.unlisted_violations({v}, set()) == {v}

    def test_violacao_listada_passa(self) -> None:
        """Violação presente na allowlist não é reportada."""
        v = ("presentation/legado.py", "infrastructure")
        assert guardrail.unlisted_violations({v}, {v}) == set()

    def test_entrada_obsoleta_reprova(self) -> None:
        """Entrada da allowlist sem violação é reportada."""
        v = ("presentation/legado.py", "infrastructure")
        assert guardrail.stale_allowlist_entries(set(), {v}) == {v}

    def test_entrada_correspondente_passa(self) -> None:
        """Entrada com violação correspondente não é reportada."""
        v = ("presentation/legado.py", "infrastructure")
        assert guardrail.stale_allowlist_entries({v}, {v}) == set()
