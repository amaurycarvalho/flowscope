"""Testes headless do trabalho puro do resumo em lote."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from flowscope.application.avaliar_guidance import AvaliarGuidanceUseCase
from flowscope.application.cancellation import (
    CancellationToken,
    OperacaoCancelada,
)
from flowscope.application.document_preview import (
    ExtracaoTexto,
    StatusExtracao,
)
from flowscope.application.documentos.document_guidance import GuidanceService
from flowscope.application.resumo_documento import ResumoDocumento
from flowscope.domain.documents import DocumentoArquivo
from flowscope.domain.fii import Guidance
from flowscope.presentation.gui.background.context import JobContext
from flowscope.presentation.gui.background.events import Erro, Progresso, Resultado
from flowscope.presentation.gui.background.job import JobHandle, Politica
from flowscope.presentation.gui.resumos_job import (
    FASE_PREPARAR,
    FASE_RESUMIR,
    _preparar_textos,
    _resumir,
    executar_resumos,
)

GUIDANCE = Guidance(
    valor_min=Decimal("0.85"),
    valor_max=Decimal("0.85"),
    periodo="2S26",
    data_relatorio=date(2026, 2, 1),
)


def _arquivo(nome: str) -> DocumentoArquivo:
    return DocumentoArquivo(
        ticker="ALZR11",
        ano=2026,
        mes=2,
        categoria="Aviso aos Acionistas",
        nome=nome,
        tipo="pdf",
        caminho=Path("/tmp") / nome,
    )


def _contexto(token=None):
    handle = JobHandle(
        id=1, grupo="resumos", politica=Politica.LATEST_WINS
    )
    if token is not None:
        handle.token = token
    eventos = []
    return JobContext(handle, eventos.append), eventos


class _PainelFake:
    def __init__(
        self,
        textos,
        falha_preparar=None,
        falha_resumir=None,
        falha_guidance=None,
    ):
        self._textos = textos
        self._falha_preparar = falha_preparar
        self._falha_resumir = falha_resumir
        self._falha_guidance = falha_guidance
        self.preparados: list[str] = []
        self.gerados: list[str] = []
        self.guidances: list[tuple[str, str]] = []

    def preparar_texto(self, arquivo, senha=None):
        if self._falha_preparar == arquivo.nome:
            raise RuntimeError("conversão falhou")
        self.preparados.append(arquivo.nome)
        texto = self._textos.get(arquivo.nome, "")
        status = StatusExtracao.OK if texto else StatusExtracao.SEM_TEXTO
        return ExtracaoTexto(texto, status)

    def persistir_no_lote(self):
        return False

    def gerar_resumo_estrito(self, arquivo, texto):
        if self._falha_resumir == arquivo.nome:
            raise RuntimeError("llm falhou")
        self.gerados.append(arquivo.nome)
        return ResumoDocumento("curto", "longo")

    def avaliar_guidance(self, arquivo, texto):
        if self._falha_guidance == arquivo.nome:
            raise RuntimeError("guidance falhou")
        self.guidances.append((arquivo.nome, texto))


class TestResumosPendentes:
    def test_duas_fases_com_progresso_e_resultados(self):
        arquivos = [_arquivo("10.pdf"), _arquivo("20.pdf")]
        painel = _PainelFake({"10.pdf": "texto A", "20.pdf": "texto B"})
        ctx, eventos = _contexto()

        sem_texto = executar_resumos(ctx, painel, arquivos)

        progressos = [e for e in eventos if isinstance(e, Progresso)]
        resultados = [e for e in eventos if isinstance(e, Resultado)]
        assert {p.dados for p in progressos} == {1, 2}
        assert any(p.dados == 1 and p.detalhe == FASE_PREPARAR for p in progressos)
        assert any(p.dados == 2 and p.detalhe == FASE_RESUMIR for p in progressos)
        assert [r.dados.nome for r in resultados] == ["10.pdf", "20.pdf"]
        assert sem_texto == 0

    def test_pula_documento_sem_texto(self):
        arquivos = [_arquivo("10.pdf"), _arquivo("20.pdf")]
        painel = _PainelFake({"10.pdf": "texto", "20.pdf": ""})
        ctx, eventos = _contexto()

        sem_texto = executar_resumos(ctx, painel, arquivos)

        resultados = [e for e in eventos if isinstance(e, Resultado)]
        assert [r.dados.nome for r in resultados] == ["10.pdf"]
        assert sem_texto == 1

    def test_erro_na_preparacao_interrompe(self):
        arquivos = [_arquivo("10.pdf"), _arquivo("20.pdf")]
        painel = _PainelFake(
            {"10.pdf": "texto", "20.pdf": "texto"},
            falha_preparar="20.pdf",
        )
        ctx, eventos = _contexto()

        executar_resumos(ctx, painel, arquivos)

        erros = [e for e in eventos if isinstance(e, Erro)]
        resultados = [e for e in eventos if isinstance(e, Resultado)]
        assert [e.dados.nome for e in erros] == ["20.pdf"]
        assert resultados == []
        assert painel.gerados == []

    def test_erro_no_resumo_interrompe_sem_processar_seguintes(self):
        arquivos = [
            _arquivo("10.pdf"), _arquivo("20.pdf"), _arquivo("30.pdf")
        ]
        painel = _PainelFake(
            {"10.pdf": "t", "20.pdf": "t", "30.pdf": "t"},
            falha_resumir="20.pdf",
        )
        ctx, eventos = _contexto()

        executar_resumos(ctx, painel, arquivos)

        resultados = [e for e in eventos if isinstance(e, Resultado)]
        erros = [e for e in eventos if isinstance(e, Erro)]
        assert [r.dados.nome for r in resultados] == ["10.pdf"]
        assert [e.dados.nome for e in erros] == ["20.pdf"]
        assert "30.pdf" not in painel.gerados


class TestGuidanceNoLote:
    def test_avalia_guidance_apos_preparar_texto(self):
        arquivos = [_arquivo("10.pdf"), _arquivo("20.pdf")]
        painel = _PainelFake({"10.pdf": "texto A", "20.pdf": "texto B"})
        ctx, _ = _contexto()

        executar_resumos(ctx, painel, arquivos)

        assert painel.guidances == [("10.pdf", "texto A"), ("20.pdf", "texto B")]

    def test_sem_texto_nao_avalia_guidance(self):
        arquivos = [_arquivo("10.pdf"), _arquivo("20.pdf")]
        painel = _PainelFake({"10.pdf": "texto", "20.pdf": ""})
        ctx, _ = _contexto()

        executar_resumos(ctx, painel, arquivos)

        assert painel.guidances == [("10.pdf", "texto")]

    def test_falha_na_avaliacao_nao_interrompe_o_lote(self):
        arquivos = [_arquivo("10.pdf"), _arquivo("20.pdf")]
        painel = _PainelFake(
            {"10.pdf": "texto A", "20.pdf": "texto B"},
            falha_guidance="20.pdf",
        )
        ctx, eventos = _contexto()

        executar_resumos(ctx, painel, arquivos)

        resultados = [e for e in eventos if isinstance(e, Resultado)]
        assert [r.dados.nome for r in resultados] == ["10.pdf", "20.pdf"]
        assert painel.guidances == [("10.pdf", "texto A")]


class _PainelPersistente(_PainelFake):
    """Painel fake que grava no worker e opcionalmente cancela após cada item."""

    def __init__(self, textos, store, token=None):
        super().__init__(textos)
        self._store = store
        self._token = token

    def persistir_no_lote(self):
        return True

    def gerar_e_persistir(self, arquivo, texto):
        resumo = super().gerar_resumo_estrito(arquivo, texto)
        self._store[arquivo.nome] = resumo
        if self._token is not None:
            self._token.request()
        return resumo


class TestPersistenciaNoWorker:
    def test_resultado_publicado_ja_esta_persistido(self):
        arquivos = [_arquivo("10.pdf"), _arquivo("20.pdf")]
        store: dict = {}
        painel = _PainelPersistente({"10.pdf": "A", "20.pdf": "B"}, store)
        ctx, eventos = _contexto()

        executar_resumos(ctx, painel, arquivos)

        resultados = [e for e in eventos if isinstance(e, Resultado)]
        assert set(store) == {"10.pdf", "20.pdf"}
        for evento in resultados:
            assert store[evento.dados.nome] is evento.valor

    def test_cancelamento_preserva_resumos_ja_gerados(self):
        arquivos = [_arquivo("10.pdf"), _arquivo("20.pdf"), _arquivo("30.pdf")]
        token = CancellationToken()
        store: dict = {}
        painel = _PainelPersistente(
            {"10.pdf": "A", "20.pdf": "B", "30.pdf": "C"}, store, token
        )
        ctx, _ = _contexto(token)

        executar_resumos(ctx, painel, arquivos)

        assert set(store) == {"10.pdf"}


class _StoreFake:
    def __init__(self):
        self._dados = {}
        self.salvos = []

    def obter(self, ticker):
        return self._dados.get(ticker)

    def salvar(self, ticker, guidance):
        self._dados[ticker] = guidance
        self.salvos.append((ticker, guidance))


class _ExtratorFake:
    def __init__(self, resultado):
        self.resultado = resultado
        self.chamadas = []

    def __call__(self, texto, data_relatorio, caminho_pdf):
        self.chamadas.append((texto, data_relatorio, caminho_pdf))
        return self.resultado


class _PainelComGuidance(_PainelFake):
    """Painel cuja avaliação de guidance usa o serviço real."""

    def __init__(self, textos, store, extrator):
        super().__init__(textos)
        self.service = GuidanceService(
            store, avaliador=AvaliarGuidanceUseCase(store, extrator)
        )

    def avaliar_guidance(self, arquivo, texto):
        self.service.avaliar(arquivo, texto)


def _arquivo_relatorio(nome: str) -> DocumentoArquivo:
    return DocumentoArquivo(
        ticker="ALZR11",
        ano=2026,
        mes=2,
        categoria="Relatorio",
        nome=nome,
        tipo="pdf",
        caminho=Path("/tmp") / nome,
    )


class TestGuidanceRealNoLote:
    def test_relatorio_pendente_com_texto_grava(self):
        arquivos = [_arquivo_relatorio("10.pdf")]
        store = _StoreFake()
        extrator = _ExtratorFake(GUIDANCE)
        painel = _PainelComGuidance({"10.pdf": "texto"}, store, extrator)
        ctx, _ = _contexto()

        executar_resumos(ctx, painel, arquivos)

        assert [ticker for ticker, _ in store.salvos] == ["ALZR11"]

    def test_documento_sem_texto_nao_avalia(self):
        arquivos = [_arquivo_relatorio("10.pdf")]
        store = _StoreFake()
        extrator = _ExtratorFake(GUIDANCE)
        painel = _PainelComGuidance({"10.pdf": ""}, store, extrator)
        ctx, _ = _contexto()

        executar_resumos(ctx, painel, arquivos)

        assert store.salvos == []
        assert extrator.chamadas == []

    def test_documento_de_outra_categoria_nao_grava(self):
        arquivos = [_arquivo("10.pdf")]
        store = _StoreFake()
        extrator = _ExtratorFake(GUIDANCE)
        painel = _PainelComGuidance({"10.pdf": "texto"}, store, extrator)
        ctx, _ = _contexto()

        executar_resumos(ctx, painel, arquivos)

        assert store.salvos == []


class _PainelQueCancela(_PainelFake):
    """Painel fake que solicita cancelamento após preparar/gerar cada item."""

    def __init__(self, textos, token):
        super().__init__(textos)
        self._token = token

    def preparar_texto(self, arquivo, senha=None):
        texto = super().preparar_texto(arquivo, senha)
        self._token.request()
        return texto

    def gerar_resumo_estrito(self, arquivo, texto):
        resumo = super().gerar_resumo_estrito(arquivo, texto)
        self._token.request()
        return resumo


class _PainelNaoDefinitivo:
    """Painel fake que devolve um resultado não definitivo no preparo."""

    def __init__(self, status):
        self._status = status
        self.gerados: list[str] = []
        self.guidances: list[str] = []

    def preparar_texto(self, arquivo, senha=None):
        texto = "parcial" if self._status is StatusExtracao.PARCIAL else ""
        return ExtracaoTexto(texto, self._status, 1)

    def persistir_no_lote(self):
        return False

    def gerar_resumo_estrito(self, arquivo, texto):
        self.gerados.append(arquivo.nome)
        return ResumoDocumento("curto", "longo")

    def avaliar_guidance(self, arquivo, texto):
        self.guidances.append(arquivo.nome)


class TestNaoDefinitivosNoLote:
    @pytest.mark.parametrize(
        "status",
        [
            StatusExtracao.PARCIAL,
            StatusExtracao.FALHA,
            StatusExtracao.PROTEGIDO,
        ],
    )
    def test_nao_definitivo_e_pulado_sem_resumir(self, status):
        arquivos = [_arquivo("10.pdf")]
        painel = _PainelNaoDefinitivo(status)
        ctx, eventos = _contexto()

        sem_texto = executar_resumos(ctx, painel, arquivos)

        assert sem_texto == 1
        assert painel.gerados == []
        assert painel.guidances == []
        assert not any(isinstance(e, Resultado) for e in eventos)


class TestCancelamento:
    def test_cancelamento_interrompe_preparacao(self):
        arquivos = [_arquivo("10.pdf"), _arquivo("20.pdf")]
        token = CancellationToken()
        painel = _PainelQueCancela(
            {"10.pdf": "texto A", "20.pdf": "texto B"}, token
        )
        ctx, _ = _contexto(token)

        with pytest.raises(OperacaoCancelada):
            _preparar_textos(ctx, painel, arquivos, False)

        assert painel.preparados == ["10.pdf"]

    def test_cancelamento_interrompe_resumo(self):
        arquivos = [_arquivo("10.pdf"), _arquivo("20.pdf")]
        token = CancellationToken()
        painel = _PainelQueCancela(
            {"10.pdf": "texto A", "20.pdf": "texto B"}, token
        )
        com_texto = [(a, painel._textos[a.nome]) for a in arquivos]
        ctx, _ = _contexto(token)

        with pytest.raises(OperacaoCancelada):
            _resumir(ctx, painel, com_texto, False)

        assert painel.gerados == ["10.pdf"]

    def test_execucao_cancelada_encerra_limpo(self):
        arquivos = [_arquivo("10.pdf"), _arquivo("20.pdf")]
        token = CancellationToken()
        painel = _PainelQueCancela(
            {"10.pdf": "texto A", "20.pdf": "texto B"}, token
        )
        ctx, eventos = _contexto(token)

        executar_resumos(ctx, painel, arquivos)

        assert painel.gerados == []
        assert not any(isinstance(e, Erro) for e in eventos)
