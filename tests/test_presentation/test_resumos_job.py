"""Testes do job de resumo em lote dos documentos pendentes."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from flowscope.application.avaliar_guidance import AvaliarGuidanceUseCase
from flowscope.application.cancellation import (
    CancellationToken,
    OperacaoCancelada,
)
from flowscope.application.documentos.document_guidance import GuidanceService
from flowscope.application.resumo_documento import ResumoDocumento
from flowscope.domain.documents import DocumentoArquivo
from flowscope.domain.fii import Guidance
from flowscope.presentation.gui.resumos_job import (
    FASE_PREPARAR,
    FASE_RESUMIR,
    MENSAGEM_ERRO,
    MENSAGEM_PROGRESSO,
    MENSAGEM_RESULTADO,
    ResumosPendentesJob,
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

    def preparar_texto(self, arquivo):
        if self._falha_preparar == arquivo.nome:
            raise RuntimeError("conversão falhou")
        self.preparados.append(arquivo.nome)
        return self._textos.get(arquivo.nome, "")

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


def _mensagens(job):
    mensagens = []
    while not job.fila.empty():
        mensagens.append(job.fila.get_nowait())
    return mensagens


class TestResumosPendentesJob:
    def test_duas_fases_com_progresso_e_resultados(self):
        arquivos = [_arquivo("10.pdf"), _arquivo("20.pdf")]
        painel = _PainelFake({"10.pdf": "texto A", "20.pdf": "texto B"})
        job = ResumosPendentesJob(painel, arquivos)
        job.iniciar().join()
        mensagens = _mensagens(job)

        progressos = [m for m in mensagens if isinstance(m, tuple) and m[0] == MENSAGEM_PROGRESSO]
        resultados = [m for m in mensagens if isinstance(m, tuple) and m[0] == MENSAGEM_RESULTADO]
        assert {m[1] for m in progressos} == {1, 2}
        assert any(m[1] == 1 and m[4] == FASE_PREPARAR for m in progressos)
        assert any(m[1] == 2 and m[4] == FASE_RESUMIR for m in progressos)
        assert [m[1].nome for m in resultados] == ["10.pdf", "20.pdf"]
        assert mensagens[-1] is True
        assert job.total == 2
        assert job.sem_texto == 0

    def test_pula_documento_sem_texto(self):
        arquivos = [_arquivo("10.pdf"), _arquivo("20.pdf")]
        painel = _PainelFake({"10.pdf": "texto", "20.pdf": ""})
        job = ResumosPendentesJob(painel, arquivos)
        job.iniciar().join()
        mensagens = _mensagens(job)

        resultados = [m for m in mensagens if isinstance(m, tuple) and m[0] == MENSAGEM_RESULTADO]
        assert [m[1].nome for m in resultados] == ["10.pdf"]
        assert job.sem_texto == 1

    def test_erro_na_preparacao_interrompe(self):
        arquivos = [_arquivo("10.pdf"), _arquivo("20.pdf")]
        painel = _PainelFake(
            {"10.pdf": "texto", "20.pdf": "texto"},
            falha_preparar="20.pdf",
        )
        job = ResumosPendentesJob(painel, arquivos)
        job.iniciar().join()
        mensagens = _mensagens(job)

        erros = [m for m in mensagens if isinstance(m, tuple) and m[0] == MENSAGEM_ERRO]
        resultados = [m for m in mensagens if isinstance(m, tuple) and m[0] == MENSAGEM_RESULTADO]
        assert [m[1].nome for m in erros] == ["20.pdf"]
        assert resultados == []
        assert painel.gerados == []
        assert mensagens[-1] is True

    def test_erro_no_resumo_interrompe_sem_processar_seguintes(self):
        arquivos = [
            _arquivo("10.pdf"), _arquivo("20.pdf"), _arquivo("30.pdf")
        ]
        painel = _PainelFake(
            {"10.pdf": "t", "20.pdf": "t", "30.pdf": "t"},
            falha_resumir="20.pdf",
        )
        job = ResumosPendentesJob(painel, arquivos)
        job.iniciar().join()
        mensagens = _mensagens(job)

        resultados = [m for m in mensagens if isinstance(m, tuple) and m[0] == MENSAGEM_RESULTADO]
        erros = [m for m in mensagens if isinstance(m, tuple) and m[0] == MENSAGEM_ERRO]
        assert [m[1].nome for m in resultados] == ["10.pdf"]
        assert [m[1].nome for m in erros] == ["20.pdf"]
        assert "30.pdf" not in painel.gerados
        assert mensagens[-1] is True


class TestGuidanceNoLote:
    def test_avalia_guidance_apos_preparar_texto(self):
        arquivos = [_arquivo("10.pdf"), _arquivo("20.pdf")]
        painel = _PainelFake({"10.pdf": "texto A", "20.pdf": "texto B"})
        job = ResumosPendentesJob(painel, arquivos)
        job.iniciar().join()
        assert painel.guidances == [("10.pdf", "texto A"), ("20.pdf", "texto B")]

    def test_sem_texto_nao_avalia_guidance(self):
        arquivos = [_arquivo("10.pdf"), _arquivo("20.pdf")]
        painel = _PainelFake({"10.pdf": "texto", "20.pdf": ""})
        job = ResumosPendentesJob(painel, arquivos)
        job.iniciar().join()
        assert painel.guidances == [("10.pdf", "texto")]

    def test_falha_na_avaliacao_nao_interrompe_o_lote(self):
        arquivos = [_arquivo("10.pdf"), _arquivo("20.pdf")]
        painel = _PainelFake(
            {"10.pdf": "texto A", "20.pdf": "texto B"},
            falha_guidance="20.pdf",
        )
        job = ResumosPendentesJob(painel, arquivos)
        job.iniciar().join()
        mensagens = _mensagens(job)
        resultados = [
            m
            for m in mensagens
            if isinstance(m, tuple) and m[0] == MENSAGEM_RESULTADO
        ]
        assert [m[1].nome for m in resultados] == ["10.pdf", "20.pdf"]
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
        job = ResumosPendentesJob(painel, arquivos)
        job.iniciar().join()
        mensagens = _mensagens(job)

        resultados = [
            m
            for m in mensagens
            if isinstance(m, tuple) and m[0] == MENSAGEM_RESULTADO
        ]
        assert set(store) == {"10.pdf", "20.pdf"}
        for _tipo, arquivo, resumo in resultados:
            assert store[arquivo.nome] is resumo

    def test_cancelamento_preserva_resumos_ja_gerados(self):
        arquivos = [_arquivo("10.pdf"), _arquivo("20.pdf"), _arquivo("30.pdf")]
        token = CancellationToken()
        store: dict = {}
        painel = _PainelPersistente(
            {"10.pdf": "A", "20.pdf": "B", "30.pdf": "C"}, store, token
        )
        job = ResumosPendentesJob(painel, arquivos, cancel_token=token)
        job.iniciar().join()

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
        job = ResumosPendentesJob(painel, arquivos)
        job.iniciar().join()
        assert [ticker for ticker, _ in store.salvos] == ["ALZR11"]

    def test_documento_sem_texto_nao_avalia(self):
        arquivos = [_arquivo_relatorio("10.pdf")]
        store = _StoreFake()
        extrator = _ExtratorFake(GUIDANCE)
        painel = _PainelComGuidance({"10.pdf": ""}, store, extrator)
        job = ResumosPendentesJob(painel, arquivos)
        job.iniciar().join()
        assert store.salvos == []
        assert extrator.chamadas == []

    def test_documento_de_outra_categoria_nao_grava(self):
        arquivos = [_arquivo("10.pdf")]
        store = _StoreFake()
        extrator = _ExtratorFake(GUIDANCE)
        painel = _PainelComGuidance({"10.pdf": "texto"}, store, extrator)
        job = ResumosPendentesJob(painel, arquivos)
        job.iniciar().join()
        assert store.salvos == []


class _PainelQueCancela(_PainelFake):
    """Painel fake que solicita cancelamento após preparar/gerar cada item."""

    def __init__(self, textos, token):
        super().__init__(textos)
        self._token = token

    def preparar_texto(self, arquivo):
        texto = super().preparar_texto(arquivo)
        self._token.request()
        return texto

    def gerar_resumo_estrito(self, arquivo, texto):
        resumo = super().gerar_resumo_estrito(arquivo, texto)
        self._token.request()
        return resumo


class TestCancelamento:
    def test_cancelamento_interrompe_preparacao(self):
        arquivos = [_arquivo("10.pdf"), _arquivo("20.pdf")]
        token = CancellationToken()
        painel = _PainelQueCancela(
            {"10.pdf": "texto A", "20.pdf": "texto B"}, token
        )
        job = ResumosPendentesJob(painel, arquivos, cancel_token=token)

        with pytest.raises(OperacaoCancelada):
            job._preparar_textos()

        assert painel.preparados == ["10.pdf"]

    def test_cancelamento_interrompe_resumo(self):
        arquivos = [_arquivo("10.pdf"), _arquivo("20.pdf")]
        token = CancellationToken()
        painel = _PainelQueCancela(
            {"10.pdf": "texto A", "20.pdf": "texto B"}, token
        )
        com_texto = [(a, painel._textos[a.nome]) for a in arquivos]
        job = ResumosPendentesJob(painel, arquivos, cancel_token=token)

        with pytest.raises(OperacaoCancelada):
            job._resumir(com_texto)

        assert painel.gerados == ["10.pdf"]

    def test_job_cancelado_encerra_limpo(self):
        arquivos = [_arquivo("10.pdf"), _arquivo("20.pdf")]
        token = CancellationToken()
        painel = _PainelQueCancela(
            {"10.pdf": "texto A", "20.pdf": "texto B"}, token
        )
        job = ResumosPendentesJob(painel, arquivos, cancel_token=token)
        thread = job.iniciar()
        thread.join(timeout=2)

        assert not thread.is_alive()
        assert _mensagens(job)[-1] is True
        assert painel.gerados == []
