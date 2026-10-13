"""Testes headless da orquestração do resumo em lote (pendentes e guidance)."""

import logging
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from flowscope.application.document_preview import StatusExtracao
from flowscope.application.finalizacao_extracao import ItemPendente
from flowscope.application.resumo_documento import ResumoDocumento
from flowscope.domain.documents import DocumentoArquivo
from flowscope.domain.fii import AvaliacaoGuidance
from flowscope.domain.llm import LLMRateLimitError
from flowscope.presentation.gui.app_resumos_actions import ResumosActionsMixin
from flowscope.presentation.gui.background.events import Erro, Outcome, Resultado
from flowscope.presentation.gui.resumos_job import ResultadoResumos

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

        host._finalizar_resumos_job(Outcome.SUCESSO, None, ResultadoResumos())

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
        host._finalizar_resumos_job(Outcome.SUCESSO, None, ResultadoResumos())
        assert host.agendados
        host.agendados[0]()
        assert host.documentos == ["HGBS11"]


def _item(status: StatusExtracao, nome: str = "10.pdf") -> ItemPendente:
    return ItemPendente(_arquivo(nome), status, "texto parcial", 1)


class _BackgroundFake:
    """Gerenciador fake com limite de inatividade em memória."""

    def __init__(self) -> None:
        self.limite_inatividade_s = 120.0
        self.definidos: list = []

    def definir_limite_inatividade(self, segundos):
        self.limite_inatividade_s = segundos
        self.definidos.append(segundos)


class _HostConfirmacao(ResumosActionsMixin):
    """Host headless que registra as decisões da confirmação de finalização."""

    def __init__(self, *, continuar: bool = False) -> None:
        self._resumos_continuar = continuar
        self._resumos_cota = False
        self._resumos_interrompido = False
        self._ticker_selecionado = "HGBS11"
        self._resumos_painel = MagicMock()
        self._resumos_painel._solicitar_senha = lambda arquivo: "segredo"
        self._resumos_painel._max_tentativas = lambda: 3
        self._timeout_atual = 90.0
        self.timeouts: list = []

        def _medir():
            return self._timeout_atual

        def _definir(valor):
            self._timeout_atual = valor
            self.timeouts.append(valor)

        self._resumos_painel.timeout_extracao = _medir
        self._resumos_painel.definir_timeout_extracao = _definir
        self._background = _BackgroundFake()
        self.agendados: list = []
        self.lotes: list = []
        self.finalizacoes: list = []
        self._flash_status = MagicMock()
        self._set_status = MagicMock()

    def after(self, ms, callback):
        self.agendados.append(callback)
        return "id"

    def _ticker_apresentado(self):
        return self._ticker_selecionado

    def _data_referencia(self):
        return date(2026, 2, 1)

    def _iniciar_lote_resumos(
        self, painel, pendentes, guarda, continuar=False, senhas=None
    ):
        self.lotes.append((painel, pendentes, guarda, continuar, senhas))

    def _submeter_finalizacao(self, itens, guarda):
        self.finalizacoes.append((itens, guarda))


def _resultado(*itens: ItemPendente) -> ResultadoResumos:
    resultado = ResultadoResumos()
    for item in itens:
        if item.status is StatusExtracao.PARCIAL:
            resultado.parciais.append(item)
        elif item.status is StatusExtracao.FALHA:
            resultado.falhas.append(item)
        else:
            resultado.protegidos.append(item)
    return resultado


class TestConfirmacaoFinalizacao:
    def _patch(self, monkeypatch, respostas):
        respostas = list(respostas)

        def fake(*args, **kwargs):
            return respostas.pop(0) if respostas else False

        monkeypatch.setattr(
            "flowscope.presentation.gui.app_resumos_actions.messagebox.askyesno",
            fake,
        )

    def test_agendada_apos_termino_normal_com_nao_conclusivos(self):
        host = _HostConfirmacao()
        host._resumos_total = 1
        host._resumos_resumidos = 0

        host._finalizar_resumos_job(
            Outcome.SUCESSO, "HGBS11", _resultado(_item(StatusExtracao.PARCIAL))
        )

        assert len(host.agendados) == 2

    def test_termino_abortado_agenda_confirmacao(self):
        host = _HostConfirmacao()
        host._resumos_total = 1

        host._finalizar_resumos_job(
            Outcome.ABORTADO, "HGBS11", _resultado(_item(StatusExtracao.PARCIAL))
        )

        assert len(host.agendados) == 2

    def test_termino_abortado_agenda_retry_do_lote(self):
        host = _HostConfirmacao()
        host._resumos_total = 3
        host._resumos_pendentes = [_arquivo("10.pdf"), _arquivo("20.pdf")]

        host._finalizar_resumos_job(
            Outcome.ABORTADO, "HGBS11", ResultadoResumos()
        )

        assert len(host.agendados) == 2

    def test_retry_do_lote_interrompido_usa_lista_do_lote(self, monkeypatch):
        self._patch(monkeypatch, [True])
        host = _HostConfirmacao()
        arquivos = [_arquivo("10.pdf"), _arquivo("20.pdf")]

        host._confirmar_finalizacao(
            ResultadoResumos(), "HGBS11", retry=arquivos
        )

        assert [a.nome for a in host.lotes[0][1]] == ["10.pdf", "20.pdf"]

    def test_timeout_nao_oferece_definitivo(self, monkeypatch):
        self._patch(monkeypatch, [False])
        host = _HostConfirmacao()

        host._confirmar_finalizacao(
            ResultadoResumos(), "HGBS11", retry=[_arquivo("10.pdf")]
        )

        assert not host.finalizacoes and not host.lotes

    def test_retry_escala_timeouts_em_30_por_cento(self, monkeypatch):
        self._patch(monkeypatch, [True])
        host = _HostConfirmacao()

        host._confirmar_finalizacao(
            _resultado(_item(StatusExtracao.PARCIAL)), "HGBS11"
        )

        assert host.timeouts == [pytest.approx(117.0)]
        assert host._background.definidos == [pytest.approx(156.0)]

    def test_retry_escala_relativo_ao_timeout_anterior(self, monkeypatch):
        self._patch(monkeypatch, [True])
        host = _HostConfirmacao()
        host._timeout_atual = 117.0
        host._background.limite_inatividade_s = 156.0

        host._confirmar_finalizacao(
            _resultado(_item(StatusExtracao.PARCIAL)), "HGBS11"
        )

        assert host.timeouts == [pytest.approx(152.1)]
        assert host._background.definidos == [pytest.approx(202.8)]

    def test_recusa_do_retry_leva_a_finalizacao(self, monkeypatch):
        self._patch(monkeypatch, [False, True])
        host = _HostConfirmacao()

        host._confirmar_finalizacao(
            _resultado(_item(StatusExtracao.PARCIAL)), "HGBS11"
        )

        assert host.finalizacoes and not host.lotes

    def test_dupla_recusa_nao_altera(self, monkeypatch):
        self._patch(monkeypatch, [False, False])
        host = _HostConfirmacao()

        host._confirmar_finalizacao(
            _resultado(_item(StatusExtracao.FALHA)), "HGBS11"
        )

        assert not host.finalizacoes and not host.lotes

    def test_confirmar_retry_reprocessa_apenas_a_lista(self, monkeypatch):
        self._patch(monkeypatch, [True])
        host = _HostConfirmacao()

        host._confirmar_finalizacao(
            _resultado(_item(StatusExtracao.PARCIAL, "10.pdf")), "HGBS11"
        )

        assert len(host.lotes) == 1
        arquivos = host.lotes[0][1]
        assert [a.nome for a in arquivos] == ["10.pdf"]

    def test_pre_coleta_de_senha_dos_protegidos(self, monkeypatch):
        self._patch(monkeypatch, [True])
        host = _HostConfirmacao()

        host._confirmar_finalizacao(
            _resultado(_item(StatusExtracao.PROTEGIDO, "20.pdf")), "HGBS11"
        )

        assert host.lotes[0][4] == {Path("/cache/20.pdf"): "segredo"}

    def test_protegido_sem_senha_nao_e_repassado(self, monkeypatch):
        self._patch(monkeypatch, [True])
        host = _HostConfirmacao()
        host._resumos_painel._solicitar_senha = lambda arquivo: None

        host._confirmar_finalizacao(
            _resultado(_item(StatusExtracao.PROTEGIDO, "20.pdf")), "HGBS11"
        )

        assert host.lotes[0][4] == {}

    def test_sem_confirmacao_por_cota(self, monkeypatch):
        self._patch(monkeypatch, [True])
        host = _HostConfirmacao()
        host._resumos_cota = True

        host._confirmar_finalizacao(
            _resultado(_item(StatusExtracao.PARCIAL)), "HGBS11"
        )

        assert not host.lotes and not host.finalizacoes

    def test_sem_confirmacao_por_erro(self, monkeypatch):
        self._patch(monkeypatch, [True])
        host = _HostConfirmacao()
        host._resumos_interrompido = True

        host._confirmar_finalizacao(
            _resultado(_item(StatusExtracao.PARCIAL)), "HGBS11"
        )

        assert not host.lotes and not host.finalizacoes

    def test_sem_confirmacao_por_troca_de_ticker(self, monkeypatch):
        self._patch(monkeypatch, [True])
        host = _HostConfirmacao()

        host._confirmar_finalizacao(
            _resultado(_item(StatusExtracao.PARCIAL)), "PETR4"
        )

        assert not host.lotes and not host.finalizacoes

    def test_sem_confirmacao_por_troca_de_periodo(self, monkeypatch):
        self._patch(monkeypatch, [True])
        host = _HostConfirmacao(continuar=True)

        host._confirmar_finalizacao(
            _resultado(_item(StatusExtracao.PARCIAL)), date(2026, 1, 1)
        )

        assert not host.lotes and not host.finalizacoes

    def test_itens_nao_finalizaveis_sao_ignorados(self, monkeypatch):
        self._patch(monkeypatch, [True])
        host = _HostConfirmacao()
        resultado = ResultadoResumos(sem_texto=1)
        resultado.parciais.append(
            ItemPendente(_arquivo("10.pdf"), StatusExtracao.OK)
        )

        host._confirmar_finalizacao(resultado, "HGBS11")

        assert not host.lotes and not host.finalizacoes

    def test_termino_cancelado_nao_agenda_confirmacao(self):
        host = _HostConfirmacao()
        host._resumos_total = 1

        host._finalizar_resumos_job(
            Outcome.CANCELADO, "HGBS11", _resultado(_item(StatusExtracao.PARCIAL))
        )

        assert len(host.agendados) == 1

    def test_termino_com_falha_fatal_nao_agenda_confirmacao(self):
        host = _HostConfirmacao()
        host._resumos_total = 1

        host._finalizar_resumos_job(
            Outcome.FALHA, "HGBS11", _resultado(_item(StatusExtracao.PARCIAL))
        )

        assert len(host.agendados) == 1


class TestFinalizarRefleteNoPainel:
    def test_finalizar_finalizacao_remonta_e_reavalia_botao(self):
        host = _HostRemontagem(continuar=False)

        host._finalizar_finalizacao()

        assert host.agendados
        host.agendados[-1]()
        assert host.documentos == ["HGBS11"]
        host._resumos_painel.refresh_resumir_button.assert_called()
