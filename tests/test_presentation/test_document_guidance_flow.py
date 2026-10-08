"""Testes da integração do gatilho de guidance ao fluxo de leitura."""

from pathlib import Path

from flowscope.application.document_preview import (
    ExtracaoTexto,
    StatusExtracao,
)
from flowscope.domain.documents import DocumentoArquivo
from flowscope.presentation.gui.background.context import JobContext
from flowscope.presentation.gui.background.events import Resultado
from flowscope.presentation.gui.background.job import JobHandle, Politica
from flowscope.presentation.gui.charts.document_flow_mixin import DocumentFlowMixin

_TEXTO_OK = ExtracaoTexto("texto preparado", StatusExtracao.OK)


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
    def __init__(
        self,
        erro: Exception | None = None,
        erro_avaliar: Exception | None = None,
        precisa: bool = True,
    ) -> None:
        self.chamadas: list[tuple[DocumentoArquivo, str | None, object]] = []
        self.erro = erro
        self.erro_avaliar = erro_avaliar
        self._precisa = precisa

    def avaliar(self, arquivo, texto, resumo=None):
        self.chamadas.append((arquivo, texto, resumo))
        if self.erro_avaliar is not None:
            raise self.erro_avaliar
        return None

    def precisa(self, arquivo):
        if self.erro is not None:
            raise self.erro
        return self._precisa


class _SummaryFake:
    def __init__(self, precisa: bool = True) -> None:
        self.gerados: list[tuple[DocumentoArquivo, str]] = []
        self._precisa = precisa

    def precisa_resumo(self, arquivo, texto):
        return self._precisa

    def gerar(self, arquivo, texto):
        self.gerados.append((arquivo, texto))
        return None


class _FlowFake(DocumentFlowMixin):
    def __init__(self, summary, guidance=None) -> None:
        self._summary = summary
        self._guidance = guidance
        self.preparos = 0

    def preparar_texto(self, arquivo, senha=None):
        self.preparos += 1
        return _TEXTO_OK


def _contexto():
    handle = JobHandle(id=1, grupo="preview", politica=Politica.LATEST_WINS)
    eventos = []
    return JobContext(handle, eventos.append), eventos


class TestTrabalhar:
    def test_le_cache_avalia_guidance_e_gera_resumo(self):
        summary = _SummaryFake()
        guidance = _GuidanceFake()
        fluxo = _FlowFake(summary, guidance)
        ctx, eventos = _contexto()
        fluxo._trabalhar(ctx, _arquivo())
        assert fluxo.preparos == 1
        assert guidance.chamadas == [(_arquivo(), "texto preparado", None)]
        assert summary.gerados == [(_arquivo(), "texto preparado")]
        assert eventos == [Resultado(valor=(_TEXTO_OK, True, None))]

    def test_guidance_nao_necessario_pula_avaliacao(self):
        summary = _SummaryFake()
        guidance = _GuidanceFake(precisa=False)
        fluxo = _FlowFake(summary, guidance)
        ctx, eventos = _contexto()
        fluxo._trabalhar(ctx, _arquivo())
        assert guidance.chamadas == []
        assert summary.gerados == [(_arquivo(), "texto preparado")]
        assert eventos == [Resultado(valor=(_TEXTO_OK, True, None))]

    def test_falha_ao_consultar_guidance_nao_interrompe_o_resumo(self):
        summary = _SummaryFake()
        guidance = _GuidanceFake(erro=RuntimeError("falha"))
        fluxo = _FlowFake(summary, guidance)
        ctx, eventos = _contexto()
        fluxo._trabalhar(ctx, _arquivo())
        assert summary.gerados == [(_arquivo(), "texto preparado")]
        assert eventos == [Resultado(valor=(_TEXTO_OK, True, None))]

    def test_falha_ao_avaliar_guidance_nao_interrompe_o_resumo(self):
        summary = _SummaryFake()
        guidance = _GuidanceFake(erro_avaliar=RuntimeError("falha"))
        fluxo = _FlowFake(summary, guidance)
        ctx, eventos = _contexto()
        fluxo._trabalhar(ctx, _arquivo())
        assert summary.gerados == [(_arquivo(), "texto preparado")]
        assert eventos == [Resultado(valor=(_TEXTO_OK, True, None))]

    def test_sem_servico_de_guidance_nao_quebra(self):
        summary = _SummaryFake()
        fluxo = _FlowFake(summary, None)
        ctx, eventos = _contexto()
        fluxo._trabalhar(ctx, _arquivo())
        assert summary.gerados == [(_arquivo(), "texto preparado")]
        assert eventos == [Resultado(valor=(_TEXTO_OK, True, None))]


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
