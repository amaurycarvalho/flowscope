"""Testes headless da orquestração do resumo em lote (pendentes e guidance)."""

import logging
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

from flowscope.application.resumo_documento import ResumoDocumento
from flowscope.domain.documents import DocumentoArquivo
from flowscope.domain.fii import AvaliacaoGuidance
from flowscope.domain.llm import LLMRateLimitError
from flowscope.presentation.gui.app_resumos_actions import ResumosActionsMixin
from flowscope.presentation.gui.background.events import Erro, Resultado

_AVALIACAO = AvaliacaoGuidance(
    metodo="ia", data_relatorio=date(2026, 2, 1)
)


def _arquivo(nome: str) -> DocumentoArquivo:
    return DocumentoArquivo(
        ticker="HGBS11",
        ano=2026,
        mes=2,
        categoria="Relatorio",
        nome=nome,
        tipo="pdf",
        caminho=Path("/cache") / nome,
        long_summary="longo",
    )


class _Host(ResumosActionsMixin):
    def __init__(self, painel, ticker: str | None = "HGBS11") -> None:
        self._documents_panel = painel
        self._resumos_painel = painel
        self._ticker_selecionado = ticker
        self._background = None
        self._resumos_persistir_worker = True
        self.lote = None

    def _ticker_apresentado(self):
        return self._ticker_selecionado

    def _iniciar_lote_resumos(self, painel, pendentes, guarda, continuar=False):
        self.lote = (painel, pendentes, guarda, continuar)


class TestResumirDocumentosPendentes:
    def test_une_sem_resumo_e_pendentes_de_guidance(self):
        painel = MagicMock()
        sem_resumo = _arquivo("10.pdf")
        pendente = _arquivo("20.pdf")
        painel.documentos_sem_resumo.return_value = [sem_resumo]
        painel.documentos_pendentes_guidance.return_value = [pendente]
        host = _Host(painel)

        host._resumir_documentos_pendentes()

        assert host.lote is not None
        assert host.lote[1] == [sem_resumo, pendente]

    def test_sem_pendentes_reavalia_o_botao_e_nao_lanca_lote(self):
        painel = MagicMock()
        painel.documentos_sem_resumo.return_value = []
        painel.documentos_pendentes_guidance.return_value = []
        host = _Host(painel)

        host._resumir_documentos_pendentes()

        painel.refresh_resumir_button.assert_called_once()
        assert host.lote is None


class TestAplicarResultadoResumo:
    def test_resumo_com_avaliacao_persistindo_no_worker(self):
        painel = MagicMock()
        host = _Host(painel)
        arquivo = _arquivo("10.pdf")
        resumo = ResumoDocumento("curto", "longo")

        host._aplicar_resultado_resumo(
            Resultado(valor=(resumo, _AVALIACAO), dados=arquivo), None
        )

        painel.refletir_resumo.assert_called_once_with(
            arquivo, resumo, _AVALIACAO
        )

    def test_resumo_com_avaliacao_sem_persistir_no_worker(self):
        painel = MagicMock()
        host = _Host(painel)
        host._resumos_persistir_worker = False
        arquivo = _arquivo("10.pdf")
        resumo = ResumoDocumento("curto", "longo")

        host._aplicar_resultado_resumo(
            Resultado(valor=(resumo, _AVALIACAO), dados=arquivo), None
        )

        painel.aplicar_resumo.assert_called_once_with(arquivo, resumo, _AVALIACAO)

    def test_sem_resumo_com_avaliacao_reflete_guidance(self):
        painel = MagicMock()
        host = _Host(painel)
        arquivo = _arquivo("20.pdf")

        host._aplicar_resultado_resumo(
            Resultado(valor=(None, _AVALIACAO), dados=arquivo), None
        )

        painel.refletir_guidance.assert_called_once_with(arquivo, _AVALIACAO)
        painel.refletir_resumo.assert_not_called()
        painel.aplicar_resumo.assert_not_called()

    def test_sem_resumo_e_sem_avaliacao_e_ignorado(self):
        painel = MagicMock()
        host = _Host(painel)
        arquivo = _arquivo("20.pdf")

        host._aplicar_resultado_resumo(
            Resultado(valor=(None, None), dados=arquivo), None
        )

        painel.refletir_guidance.assert_not_called()

    def test_guarda_divergente_descarta(self):
        painel = MagicMock()
        host = _Host(painel, ticker="HGBS11")
        arquivo = _arquivo("10.pdf")

        host._aplicar_resultado_resumo(
            Resultado(valor=(ResumoDocumento("c", "l"), None), dados=arquivo),
            "PETR4",
        )

        painel.refletir_resumo.assert_not_called()
        painel.aplicar_resumo.assert_not_called()

    def test_falha_de_guidance_conta_no_desfecho(self):
        painel = MagicMock()
        painel.guidance_falhou.return_value = True
        host = _Host(painel)
        host._resumos_falhas = 0
        arquivo = _arquivo("20.pdf")

        host._aplicar_resultado_resumo(
            Resultado(valor=(None, _AVALIACAO), dados=arquivo), None
        )

        assert host._resumos_falhas == 1

    def test_sem_falha_de_guidance_nao_conta(self):
        painel = MagicMock()
        painel.guidance_falhou.return_value = False
        host = _Host(painel)
        host._resumos_falhas = 0
        arquivo = _arquivo("20.pdf")

        host._aplicar_resultado_resumo(
            Resultado(valor=(None, _AVALIACAO), dados=arquivo), None
        )

        assert host._resumos_falhas == 0


class _HostRemontagem(ResumosActionsMixin):
    """Host headless que registra o despacho da remontagem pós-lote."""

    def __init__(self, *, continuar: bool = False) -> None:
        self._resumos_continuar = continuar
        self._resumos_cota = False
        self._ticker_selecionado = "HGBS11"
        self._resumos_painel = MagicMock()
        self.agendados: list = []
        self.documentos: list = []
        self.noticias: list = []
        self._flash_status = MagicMock()
        self._set_status = MagicMock()

    def after(self, ms, callback):
        self.agendados.append(callback)
        return "id"

    def _ticker_apresentado(self):
        return self._ticker_selecionado

    def _data_referencia(self):
        return date(2026, 2, 1)

    def _submeter_leitura_documentos(self, ticker):
        self.documentos.append(ticker)

    def _submeter_leitura_noticias(self, referencia):
        self.noticias.append(referencia)


class TestCotaEsgotadaNoLote:
    def test_marca_interrupcao_por_cota_sem_traceback(self, caplog):
        host = _HostRemontagem(continuar=True)
        with caplog.at_level(logging.WARNING):
            host._interromper_resumos(
                Erro(
                    excecao=LLMRateLimitError("Error code: 429"),
                    dados=_arquivo("10.pdf"),
                )
            )

        assert host._resumos_cota is True
        registro = caplog.records[-1]
        assert registro.levelno == logging.WARNING
        assert registro.exc_info is None
        assert "Cota da I.A. esgotada" in registro.message

    def test_desfecho_unico_de_cota(self):
        host = _HostRemontagem(continuar=True)
        host._resumos_cota = True
        host._resumos_total = 100
        host._resumos_resumidos = 7

        host._finalizar_resumos_job(False, None, 0)

        host._flash_status.assert_called_once()
        mensagem = host._flash_status.call_args.args[0]
        assert "Cota da I.A. esgotada" in mensagem
        assert "7 de 100" in mensagem

    def test_erro_transitorio_mantem_registro_com_traceback(self, caplog):
        host = _HostRemontagem(continuar=True)
        with caplog.at_level(logging.ERROR):
            host._interromper_resumos(
                Erro(excecao=RuntimeError("boom"), dados=_arquivo("10.pdf"))
            )

        assert host._resumos_cota is False
        assert caplog.records[-1].exc_info is not None


class TestRecarregarPainelResumos:
    def test_documentos_despacha_leitura(self):
        host = _HostRemontagem(continuar=False)
        host._recarregar_painel_resumos()
        assert host.documentos == ["HGBS11"]
        assert host.noticias == []

    def test_noticias_despacha_leitura(self):
        host = _HostRemontagem(continuar=True)
        host._recarregar_painel_resumos()
        assert host.noticias == [date(2026, 2, 1)]
        assert host.documentos == []


class TestFinalizarAgendaRemontagem:
    def test_agenda_recarga_do_origem(self):
        host = _HostRemontagem(continuar=False)
        host._finalizar_resumos_job(False, None, 0)
        assert host.agendados
        host.agendados[0]()
        assert host.documentos == ["HGBS11"]
