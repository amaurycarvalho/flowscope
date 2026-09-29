"""Testes da integração do gatilho de guidance ao fluxo de leitura."""

from pathlib import Path

from flowscope.domain.documents import DocumentoArquivo
from flowscope.presentation.gui.background.context import JobContext
from flowscope.presentation.gui.background.events import Resultado
from flowscope.presentation.gui.background.job import JobHandle, Politica
from flowscope.presentation.gui.charts.document_flow_mixin import DocumentFlowMixin


def _arquivo() -> DocumentoArquivo:
    return DocumentoArquivo(
        ticker="HGBS11",
        ano=2026,
        mes=8,
        categoria="Relatorio",
        nome="10.pdf",
        tipo="pdf",
        caminho=Path("/cache/relatorio/10.pdf"),
    )


class _GuidanceFake:
    def __init__(self, erro: Exception | None = None) -> None:
        self.chamadas: list[tuple[DocumentoArquivo, str | None]] = []
        self.erro = erro

    def avaliar(self, arquivo, texto):
        self.chamadas.append((arquivo, texto))
        if self.erro is not None:
            raise self.erro
        return None

    def precisa(self, arquivo):
        if self.erro is not None:
            raise self.erro
        return True


class _SummaryFake:
    def __init__(self) -> None:
        self.gerados: list[tuple[DocumentoArquivo, str]] = []

    def gerar(self, arquivo, texto):
        self.gerados.append((arquivo, texto))
        return None


class _FlowFake(DocumentFlowMixin):
    def __init__(self, summary, guidance=None) -> None:
        self._summary = summary
        self._guidance = guidance
        self.preparos = 0

    def preparar_texto(self, arquivo):
        self.preparos += 1
        return "texto preparado"


def _contexto():
    handle = JobHandle(id=1, grupo="preview", politica=Politica.LATEST_WINS)
    eventos = []
    return JobContext(handle, eventos.append), eventos


class TestTrabalhar:
    def test_avalia_guidance_e_gera_resumo(self):
        summary = _SummaryFake()
        guidance = _GuidanceFake()
        fluxo = _FlowFake(summary, guidance)
        ctx, eventos = _contexto()
        fluxo._trabalhar(ctx, _arquivo(), None)
        assert guidance.chamadas == [(_arquivo(), "texto preparado")]
        assert summary.gerados == [(_arquivo(), "texto preparado")]
        assert eventos == [Resultado(valor=("texto preparado", None))]

    def test_usa_texto_conhecido_sem_repreparar(self):
        summary = _SummaryFake()
        guidance = _GuidanceFake()
        fluxo = _FlowFake(summary, guidance)
        ctx, eventos = _contexto()
        fluxo._trabalhar(ctx, _arquivo(), "texto do cache")
        assert fluxo.preparos == 0
        assert guidance.chamadas == [(_arquivo(), "texto do cache")]
        assert eventos == [Resultado(valor=("texto do cache", None))]

    def test_falha_de_guidance_nao_interrompe_o_resumo(self):
        summary = _SummaryFake()
        guidance = _GuidanceFake(erro=RuntimeError("falha"))
        fluxo = _FlowFake(summary, guidance)
        ctx, eventos = _contexto()
        fluxo._trabalhar(ctx, _arquivo(), "texto")
        assert summary.gerados == [(_arquivo(), "texto")]
        assert eventos == [Resultado(valor=("texto", None))]

    def test_sem_servico_de_guidance_nao_quebra(self):
        summary = _SummaryFake()
        fluxo = _FlowFake(summary, None)
        ctx, eventos = _contexto()
        fluxo._trabalhar(ctx, _arquivo(), "texto")
        assert summary.gerados == [(_arquivo(), "texto")]
        assert eventos == [Resultado(valor=("texto", None))]


class TestPrecisaGuidance:
    def test_sem_servico_retorna_false(self):
        fluxo = _FlowFake(_SummaryFake(), None)
        assert fluxo._precisa_guidance(_arquivo()) is False

    def test_com_servico_consulta(self):
        fluxo = _FlowFake(_SummaryFake(), _GuidanceFake())
        assert fluxo._precisa_guidance(_arquivo()) is True

    def test_erro_no_cache_retorna_false(self):
        fluxo = _FlowFake(_SummaryFake(), _GuidanceFake(erro=RuntimeError("x")))
        assert fluxo._precisa_guidance(_arquivo()) is False
