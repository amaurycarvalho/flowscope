"""Verifica as fronteiras de dependência da camada de domínio FII."""

import ast
from pathlib import Path


def _modulos_do_pacote() -> list[Path]:
    """Lista os módulos Python do pacote ``domain/fii``."""
    raiz = Path(__file__).resolve().parents[3] / "src" / "flowscope" / "domain" / "fii"
    return sorted(raiz.glob("*.py"))


def _importa_camada_externa(conteudo: str, camada: str) -> bool:
    """Indica se o código importa algum módulo da camada externa."""
    arvore = ast.parse(conteudo)
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            for alias in no.names:
                if alias.name.startswith(f"flowscope.{camada}"):
                    return True
        if isinstance(no, ast.ImportFrom) and no.module:
            if no.module.startswith(f"flowscope.{camada}"):
                return True
    return False


class TestFronteirasDeCamada:
    def test_dominio_fii_nao_importa_application(self):
        for modulo in _modulos_do_pacote():
            if modulo.name == "__init__.py":
                continue
            conteudo = modulo.read_text(encoding="utf-8")
            assert not _importa_camada_externa(conteudo, "application"), modulo.name

    def test_dominio_fii_nao_importa_infrastructure(self):
        for modulo in _modulos_do_pacote():
            if modulo.name == "__init__.py":
                continue
            conteudo = modulo.read_text(encoding="utf-8")
            assert not _importa_camada_externa(conteudo, "infrastructure"), modulo.name

    def test_dominio_fii_nao_importa_presentation(self):
        for modulo in _modulos_do_pacote():
            if modulo.name == "__init__.py":
                continue
            conteudo = modulo.read_text(encoding="utf-8")
            assert not _importa_camada_externa(conteudo, "presentation"), modulo.name
