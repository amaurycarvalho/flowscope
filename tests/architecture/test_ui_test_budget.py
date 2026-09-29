"""Guarda de orçamento dos testes de UI gated por display.

O baseline é lido de ``ui_test_budget.txt`` (fonte do teto) e comparado à
contagem corrente da suíte de apresentação. O critério objetivo de "teste de
UI", aplicado por AST, é: declarações decoradas com ``@needs_display`` (funções
e classes) ou funções de teste que criam ``tk.Tk``/``tk.Toplevel`` sem gating.

O teto apenas encolhe: um **aumento** reprova o teste e uma **queda** exige a
atualização explícita do baseline para o valor novo. Testes de processamento
escritos sem exigir ``DISPLAY`` não contam.
"""

import ast
from pathlib import Path

_TESTS_APRESENTACAO = Path(__file__).resolve().parents[1] / "test_presentation"
_BASELINE = Path(__file__).resolve().parent / "ui_test_budget.txt"

#: Nome do marcador de gating por display.
_GATE = "needs_display"

#: Chamadas que caracterizam a criação de uma janela Tk.
_CRIAM_JANELA = {"Tk", "Toplevel"}


def _decoradores(node: ast.AST) -> set[str]:
    """Retorna os nomes dos decoradores de uma função ou classe."""
    nomes: set[str] = set()
    for decorador in getattr(node, "decorator_list", []):
        alvo = decorador.func if isinstance(decorador, ast.Call) else decorador
        if isinstance(alvo, ast.Name):
            nomes.add(alvo.id)
        elif isinstance(alvo, ast.Attribute):
            nomes.add(alvo.attr)
    return nomes


def _cria_janela(node: ast.AST) -> bool:
    """Indica se o nó cria uma janela Tk/Toplevel em algum ponto."""
    for interno in ast.walk(node):
        if not isinstance(interno, ast.Call):
            continue
        alvo = interno.func
        if isinstance(alvo, ast.Name) and alvo.id in _CRIAM_JANELA:
            return True
        if isinstance(alvo, ast.Attribute) and alvo.attr in _CRIAM_JANELA:
            return True
    return False


def _contar_corpo(corpo: list[ast.stmt], gated: bool) -> int:
    """Conta as declarações de UI em um corpo, propagando o gating da classe."""
    total = 0
    for node in corpo:
        if isinstance(node, ast.ClassDef):
            propria = _GATE in _decoradores(node)
            total += int(propria)
            total += _contar_corpo(node.body, gated or propria)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            propria = _GATE in _decoradores(node)
            if propria:
                total += 1
            elif node.name.startswith("test_") and not gated and _cria_janela(node):
                total += 1
            total += _contar_corpo(node.body, gated or propria)
    return total


def count_ui_declarations(source: str) -> int:
    """Conta as declarações de UI em um trecho de código."""
    return _contar_corpo(ast.parse(source).body, gated=False)


def count_ui_tests(root: Path) -> int:
    """Conta as declarações de UI em todos os módulos sob ``root``."""
    return sum(
        count_ui_declarations(caminho.read_text(encoding="utf-8"))
        for caminho in root.rglob("*.py")
    )


def read_baseline(path: Path) -> int:
    """Lê o baseline do arquivo, ignorando comentários e linhas vazias."""
    for linha in path.read_text(encoding="utf-8").splitlines():
        conteudo = linha.split("#", 1)[0].strip()
        if conteudo:
            return int(conteudo)
    raise ValueError(f"Baseline vazio em {path}")


def verificar_baseline(contagem: int, baseline: int) -> str | None:
    """Retorna a mensagem de erro do teto, ou ``None`` quando está no valor."""
    if contagem > baseline:
        return (
            f"Testes de UI aumentaram: {contagem} > {baseline}. Migre o "
            "processamento para testes headless; o teto não pode ser elevado."
        )
    if contagem < baseline:
        return (
            f"Testes de UI caíram: {contagem} < {baseline}. Atualize "
            f"'tests/architecture/ui_test_budget.txt' para {contagem} para "
            "consolidar a redução (o teto só encolhe)."
        )
    return None


class TestOrcamentoTestesUI:
    """Verifica o teto commitado e o comportamento de ratchet do guardrail."""

    def test_baseline_vem_do_arquivo(self, tmp_path: Path) -> None:
        arquivo = tmp_path / "baseline.txt"
        arquivo.write_text("# comentario\n123\n", encoding="utf-8")
        assert read_baseline(arquivo) == 123

    def test_arquivo_de_baseline_existe(self) -> None:
        assert _BASELINE.exists()

    def test_contagem_no_teto(self) -> None:
        contagem = count_ui_tests(_TESTS_APRESENTACAO)
        baseline = read_baseline(_BASELINE)
        erro = verificar_baseline(contagem, baseline)
        assert erro is None, erro

    def test_incremento_reprova(self) -> None:
        erro = verificar_baseline(11, 10)
        assert erro is not None and "aumentaram" in erro

    def test_queda_exige_atualizacao(self) -> None:
        erro = verificar_baseline(9, 10)
        assert erro is not None and "Atualize" in erro

    def test_valor_igual_passa(self) -> None:
        assert verificar_baseline(10, 10) is None

    def test_teste_headless_nao_conta(self) -> None:
        fonte = "def test_x():\n    assert True\n"
        assert count_ui_declarations(fonte) == 0

    def test_funcao_gated_conta(self) -> None:
        fonte = "@needs_display\ndef test_x():\n    pass\n"
        assert count_ui_declarations(fonte) == 1

    def test_classe_gated_conta_uma_vez(self) -> None:
        fonte = (
            "@needs_display\n"
            "class TestX:\n"
            "    def test_a(self):\n        pass\n"
            "    def test_b(self):\n        pass\n"
        )
        assert count_ui_declarations(fonte) == 1

    def test_cria_tk_sem_gate_conta(self) -> None:
        fonte = "import tkinter as tk\ndef test_x():\n    tk.Tk()\n"
        assert count_ui_declarations(fonte) == 1

    def test_helper_que_cria_tk_nao_conta(self) -> None:
        fonte = "import tkinter as tk\ndef helper():\n    tk.Tk()\n"
        assert count_ui_declarations(fonte) == 0

    def test_metodo_de_classe_gated_nao_conta_em_dobro(self) -> None:
        fonte = (
            "import tkinter as tk\n"
            "@needs_display\n"
            "class TestX:\n"
            "    def test_a(self):\n"
            "        tk.Tk()\n"
        )
        assert count_ui_declarations(fonte) == 1
