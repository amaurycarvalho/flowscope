"""Testes headless do fluxo de senha e de texto parcial (mixin).

Exercitam a solicitação de senha em PDFs protegidos, o limite de tentativas, a
anotação de extração parcial e a decisão de não resumir resultados parciais,
sem instanciar widgets.
"""

from pathlib import Path

from flowscope.application.document_preview import (
    SEM_TEXTO,
    ExtracaoTexto,
    StatusExtracao,
)
from flowscope.domain.documents import DocumentoArquivo
from flowscope.presentation.gui.background.context import JobContext
from flowscope.presentation.gui.background.events import Resultado
from flowscope.presentation.gui.background.job import JobHandle, Politica
from flowscope.presentation.gui.charts.document_flow_mixin import (
    MAX_TENTATIVAS_SENHA,
    DocumentFlowMixin,
)

_PROTEGIDO = ExtracaoTexto("", StatusExtracao.PROTEGIDO)
_PARCIAL = ExtracaoTexto("parte do texto", StatusExtracao.PARCIAL, 2)


def _arquivo() -> DocumentoArquivo:
    return DocumentoArquivo(
        ticker="ALZR11",
        ano=2026,
        mes=2,
        categoria="Aviso aos Acionistas",
        nome="10.pdf",
        tipo="pdf",
        caminho=Path("/tmp/10.pdf"),
    )


class _SummaryFake:
    def __init__(self) -> None:
        self.gerados: list[str] = []

    def chave(self, arquivo) -> str:
        return "ALZR11/10.pdf"

    def mensagem_indisponivel(self) -> str:
        return "Resumo indisponível."

    def resumo_para_exibir(self, arquivo, texto):
        return None

    def precisa_resumo(self, arquivo, texto) -> bool:
        return True

    def gerar(self, arquivo, texto):
        self.gerados.append(texto)
        return None


class _StoreFake:
    def __init__(self) -> None:
        self.salvos: list[tuple[str, str, str]] = []

    def obter(self, ticker, chave):
        return None

    def salvar(self, ticker, chave, texto) -> None:
        self.salvos.append((ticker, chave, texto))


class _Host(DocumentFlowMixin):
    """Host headless que intercepta widgets e submissões de background."""

    def __init__(self) -> None:
        self._summary = _SummaryFake()
        self._text_store = _StoreFake()
        self._preview_cache: dict = {}
        self._senha_interativa = True
        self._senha_max_tentativas = MAX_TENTATIVAS_SENHA
        self._senha_a_retornar: str | None = None
        self.prompts: list = []
        self.submetidos: list = []
        self.preview = ""
        self._selecionado = None
        self._resultado = _PARCIAL

    def _arquivo_selecionado(self):
        return self._selecionado

    def _iniciar_preview(self, arquivo, senha=None):
        self.submetidos.append((arquivo, senha))

    def _set_preview_text(self, texto):
        self.preview = texto

    def _atualizar_resumo(self, arquivo):
        pass

    def _solicitar_senha(self, arquivo):
        self.prompts.append(arquivo)
        return self._senha_a_retornar

    def preparar_texto(self, arquivo, senha=None):
        return self._resultado


def _contexto():
    handle = JobHandle(id=1, grupo="preview", politica=Politica.LATEST_WINS)
    eventos = []
    return JobContext(handle, eventos.append), eventos


class TestSenha:
    def test_protegido_interativo_dispara_solicitacao_e_reprocessa(self):
        host = _Host()
        host._senha_a_retornar = "abc"
        assert host._tentar_senha(_arquivo(), _PROTEGIDO) is True
        assert host.prompts == [_arquivo()]
        assert host.submetidos == [(_arquivo(), "abc")]

    def test_nao_interativo_nao_solicita(self):
        host = _Host()
        host._senha_interativa = False
        assert host._tentar_senha(_arquivo(), _PROTEGIDO) is False
        assert host.prompts == []

    def test_cancelamento_nao_reprocessa(self):
        host = _Host()
        host._senha_a_retornar = None
        assert host._tentar_senha(_arquivo(), _PROTEGIDO) is False
        assert len(host.prompts) == 1
        assert host.submetidos == []

    def test_limite_de_tres_tentativas(self):
        host = _Host()
        host._senha_a_retornar = "errada"
        for _ in range(5):
            host._tentar_senha(_arquivo(), _PROTEGIDO)
        assert len(host.prompts) == MAX_TENTATIVAS_SENHA
        assert len(host.submetidos) == MAX_TENTATIVAS_SENHA

    def test_senha_nao_e_persistida(self):
        host = _Host()
        host._senha_a_retornar = "s3cr3t"
        host._tentar_senha(_arquivo(), _PROTEGIDO)
        assert host._text_store.salvos == []

    def test_nao_protegido_nao_solicita(self):
        host = _Host()
        assert host._tentar_senha(_arquivo(), ExtracaoTexto("x", StatusExtracao.OK)) is False
        assert host.prompts == []

    def test_esgotado_exibe_ausencia(self):
        host = _Host()
        arquivo = _arquivo()
        host._senha_a_retornar = "errada"
        for _ in range(MAX_TENTATIVAS_SENHA):
            host._tentar_senha(arquivo, _PROTEGIDO)
        host._selecionado = arquivo
        host._aplicar_preview(arquivo, _PROTEGIDO, False)
        assert host.submetidos == [(arquivo, "errada")] * MAX_TENTATIVAS_SENHA
        assert host.preview == SEM_TEXTO


class TestParcial:
    def test_parcial_anotado(self):
        host = _Host()
        anotacao = host._anotacao_parcial(3)
        assert "3 página" in anotacao
        host._mostrar_documento("texto", None, anotacao)
        assert host.preview.startswith(anotacao)

    def test_parcial_nao_gera_resumo(self):
        host = _Host()
        host._resultado = _PARCIAL
        ctx, eventos = _contexto()
        host._trabalhar(ctx, _arquivo())
        assert host._summary.gerados == []
        assert eventos == [Resultado(valor=(_PARCIAL, False, None))]

    def test_completo_gera_resumo(self):
        host = _Host()
        host._resultado = ExtracaoTexto("texto completo", StatusExtracao.OK)
        ctx, eventos = _contexto()
        host._trabalhar(ctx, _arquivo())
        assert host._summary.gerados == ["texto completo"]
        assert eventos[0].valor[1] is True
