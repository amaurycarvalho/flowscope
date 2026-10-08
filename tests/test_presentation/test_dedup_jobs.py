"""Testes da integração do housekeeping de dedup aos jobs de aquisição."""

from datetime import date
from unittest.mock import MagicMock

from flowscope.application.cancellation import (
    CancellationToken,
    OperacaoCancelada,
)

from flowscope.presentation.gui.documentos_job import executar_documentos
from flowscope.presentation.gui.noticias_job import executar_noticias

_REFERENCIA = date(2026, 9, 25)


class _CtxFake:
    def __init__(self) -> None:
        self.token = CancellationToken()
        self.progressos: list[dict] = []

    def progress(self, **kwargs) -> None:
        self.progressos.append(kwargs)


class TestJobDocumentos:
    def test_dedup_roda_apos_aquisicao(self):
        ctx = _CtxFake()
        aquisicao = MagicMock()
        dedup = MagicMock()
        executar_documentos(ctx, aquisicao, "ALZR11", _REFERENCIA, dedup)
        aquisicao.adquirir.assert_called_once()
        assert dedup.call_args.args[0] == "ALZR11"
        assert dedup.call_args.args[1] is ctx.token

    def test_sem_dedup_nao_falha(self):
        ctx = _CtxFake()
        aquisicao = MagicMock()
        executar_documentos(ctx, aquisicao, "ALZR11", _REFERENCIA)
        aquisicao.adquirir.assert_called_once()

    def test_falha_do_dedup_nao_propaga(self):
        ctx = _CtxFake()
        aquisicao = MagicMock()
        dedup = MagicMock(side_effect=RuntimeError("boom"))
        executar_documentos(ctx, aquisicao, "ALZR11", _REFERENCIA, dedup)

    def test_cancelamento_do_dedup_nao_propaga(self):
        ctx = _CtxFake()
        aquisicao = MagicMock()
        dedup = MagicMock(side_effect=OperacaoCancelada())
        executar_documentos(ctx, aquisicao, "ALZR11", _REFERENCIA, dedup)

    def test_dedup_roda_mesmo_com_falha_de_aquisicao(self):
        ctx = _CtxFake()
        aquisicao = MagicMock()
        aquisicao.adquirir.side_effect = RuntimeError("offline")
        dedup = MagicMock()
        executar_documentos(ctx, aquisicao, "ALZR11", _REFERENCIA, dedup)
        dedup.assert_called_once()


class TestJobNoticias:
    def test_dedup_roda_apos_aquisicao(self):
        ctx = _CtxFake()
        aquisicao = MagicMock()
        dedup = MagicMock()
        executar_noticias(ctx, aquisicao, _REFERENCIA, dedup)
        aquisicao.adquirir.assert_called_once()
        assert dedup.call_args.args[0] is ctx.token

    def test_sem_dedup_nao_falha(self):
        ctx = _CtxFake()
        aquisicao = MagicMock()
        executar_noticias(ctx, aquisicao, _REFERENCIA)
        aquisicao.adquirir.assert_called_once()

    def test_falha_do_dedup_nao_propaga(self):
        ctx = _CtxFake()
        aquisicao = MagicMock()
        dedup = MagicMock(side_effect=RuntimeError("boom"))
        executar_noticias(ctx, aquisicao, _REFERENCIA, dedup)
