"""Testes da orquestração do botão Atualizar e das mensagens de desfecho."""

from datetime import date
from unittest.mock import MagicMock

from flowscope.application.cancellation import CancellationToken
from flowscope.application.documentos.aquisicao import ResultadoAquisicao
from flowscope.application.renda_fixa import ResultadoAquisicaoTitulos
from flowscope.presentation.gui.atualizacao_mensagens import mensagem_atualizacao
from flowscope.presentation.gui.documentos_job import (
    ResultadoAtualizacao,
    executar_atualizacao,
    executar_titulos,
)

_REFERENCIA = date(2026, 9, 30)


class _CtxFake:
    def __init__(self) -> None:
        self.token = CancellationToken()
        self.progressos: list[dict] = []

    def progress(self, **kwargs) -> None:
        self.progressos.append(kwargs)


class _TitulosFake:
    def __init__(self, resultado: ResultadoAquisicaoTitulos) -> None:
        self._resultado = resultado
        self.chamadas = 0

    def adquirir(self, ticker, reference_date, progress=None, cancel_token=None):
        self.chamadas += 1
        if progress is not None:
            progress(1, 3, "Títulos: FRE")
        return self._resultado


class TestOrquestracao:
    def test_executa_documentos_e_titulos(self):
        ctx = _CtxFake()
        documentos = MagicMock()
        documentos.adquirir.return_value = ResultadoAquisicao(novos=2)
        titulos = _TitulosFake(ResultadoAquisicaoTitulos(novos=1))
        resultado = executar_atualizacao(
            ctx, documentos, titulos, "PETR4", _REFERENCIA
        )
        assert resultado.documentos.novos == 2
        assert resultado.titulos.novos == 1
        assert titulos.chamadas == 1

    def test_falha_dos_titulos_nao_impede_documentos(self):
        ctx = _CtxFake()
        documentos = MagicMock()
        documentos.adquirir.return_value = ResultadoAquisicao(novos=1)
        titulos = _TitulosFake(ResultadoAquisicaoTitulos(falhas=1))
        resultado = executar_atualizacao(
            ctx, documentos, titulos, "PETR4", _REFERENCIA
        )
        assert resultado.documentos.novos == 1
        assert resultado.titulos.falhas == 1

    def test_falha_de_documentos_nao_impede_titulos(self):
        ctx = _CtxFake()
        documentos = MagicMock()
        documentos.adquirir.side_effect = RuntimeError("offline")
        titulos = _TitulosFake(ResultadoAquisicaoTitulos(novos=3))
        resultado = executar_atualizacao(
            ctx, documentos, titulos, "PETR4", _REFERENCIA
        )
        assert resultado.titulos.novos == 3

    def test_progresso_prefixa_etapas(self):
        ctx = _CtxFake()
        documentos = MagicMock()

        def adquirir(ticker, ref, progress, cancel_token):
            progress(1, 1, "documento")
            return ResultadoAquisicao()

        documentos.adquirir.side_effect = adquirir
        titulos = _TitulosFake(ResultadoAquisicaoTitulos())
        executar_atualizacao(ctx, documentos, titulos, "PETR4", _REFERENCIA)
        detalhes = [item["detalhe"] for item in ctx.progressos]
        assert any(item.startswith("Documentos:") for item in detalhes)
        assert any(item.startswith("Títulos:") for item in detalhes)

    def test_executar_titulos_tolera_excecao(self):
        ctx = _CtxFake()
        titulos = MagicMock()
        titulos.adquirir.side_effect = RuntimeError("offline")
        resultado = executar_titulos(ctx, titulos, "PETR4", _REFERENCIA)
        assert resultado.falhas == 1


class TestMensagens:
    def test_documentos_e_titulos(self):
        resultado = ResultadoAtualizacao(
            documentos=ResultadoAquisicao(novos=1),
            titulos=ResultadoAquisicaoTitulos(novos=1),
        )
        assert mensagem_atualizacao(resultado) == (
            "Documentos e títulos atualizados!",
            "",
        )

    def test_sem_novidades_nao_afirma_atualizacao(self):
        resultado = ResultadoAtualizacao(
            documentos=ResultadoAquisicao(reutilizados=1),
            titulos=ResultadoAquisicaoTitulos(reutilizados=1),
        )
        mensagem = mensagem_atualizacao(resultado)
        assert "atualizados" not in mensagem[0]

    def test_falha_de_titulos_distinguida_de_ausencia(self):
        resultado = ResultadoAtualizacao(
            titulos=ResultadoAquisicaoTitulos(falhas=1)
        )
        mensagem = mensagem_atualizacao(resultado)
        assert mensagem[1] == "⚠"
        assert "títulos" in mensagem[0]

    def test_sem_cnpj_nao_e_falha(self):
        resultado = ResultadoAtualizacao(
            titulos=ResultadoAquisicaoTitulos(sem_cnpj=True)
        )
        mensagem = mensagem_atualizacao(resultado)
        assert mensagem[1] == "ℹ"
        assert "CNPJ" in mensagem[0]
