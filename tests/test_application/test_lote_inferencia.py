"""Testes da fase de inferência acoplada ao lote de resumos."""

from pathlib import Path

from flowscope.application.cancellation import OperacaoCancelada
from flowscope.application.document_preview import ExtracaoTexto, StatusExtracao
from flowscope.application.documentos.lote_execucao import (
    FASE_INFERIR,
    FASE_RESUMIR,
    ResultadoResumos,
    executar_resumos,
)
from flowscope.application.renda_fixa import ResultadoInferencia
from flowscope.application.resumo_documento import ResumoDocumento
from flowscope.domain.documents import DocumentoArquivo


class _Contexto:
    def __init__(self, cancelar=False):
        self.eventos = []
        self._cancelar = cancelar

    def raise_if_cancelled(self):
        if self._cancelar:
            raise OperacaoCancelada()

    def descrever(self, texto):
        pass

    def progress(self, detalhe="", atual=None, total=None, dados=None):
        self.eventos.append((detalhe, atual, total, dados))

    def erro(self, excecao, dados=None):
        self.eventos.append(("erro", excecao, dados))

    def resultado(self, valor=None, falhou=False, dados=None):
        self.eventos.append(("resultado", valor, dados))


class _Painel:
    def preparar_texto(self, arquivo, senha=None):
        return ExtracaoTexto("texto", StatusExtracao.OK)

    def persistir_no_lote(self):
        return False

    def gerar_resumo_estrito(self, arquivo, texto):
        return ResumoDocumento("curto", "longo")

    def gerar_e_persistir(self, arquivo, texto):
        return ResumoDocumento("curto", "longo")

    def avaliar_guidance(self, arquivo, texto, resumo=None):
        return None


class _InferenciaFake:
    def __init__(self, resultado=None, erro=None):
        self.resultado = resultado or ResultadoInferencia(executada=True, itens=2)
        self.erro = erro
        self.chamadas = []

    def executar(self, ticker, progress=None, cancelar=None):
        self.chamadas.append(ticker)
        if self.erro is not None:
            raise self.erro
        if progress is not None:
            progress(1, 1, "inferência de direitos e obrigações")
        return self.resultado


def _arquivo(nome: str = "10.pdf") -> DocumentoArquivo:
    return DocumentoArquivo(
        ticker="ALZR11",
        ano=2026,
        mes=2,
        categoria="Relatorio",
        nome=nome,
        tipo="pdf",
        caminho=Path("/cache") / nome,
        long_summary="resumo.",
    )


class TestFaseInferencia:
    def test_executa_depois_dos_resumos_e_preserva_contagens(self):
        ctx = _Contexto()
        inferencia = _InferenciaFake()

        resultado = executar_resumos(
            ctx,
            _Painel(),
            [_arquivo()],
            inferencia=inferencia,
            ticker="ALZR11",
        )

        progressos = [evento for evento in ctx.eventos if len(evento) == 4]
        fases = [dados for _, _, _, dados in progressos if dados in (2, 3)]
        assert fases[-1] == 3
        assert set(fases) == {2, 3}
        assert fases.index(3) > fases.index(2)
        assert any(
            detalhe == FASE_INFERIR for detalhe, _, _, _ in progressos
        )
        assert resultado.sem_texto == 0
        assert resultado.inferencia.itens == 2
        assert inferencia.chamadas == ["ALZR11"]

    def test_inferencia_pendente_sem_documentos_executa(self):
        ctx = _Contexto()
        inferencia = _InferenciaFake()

        resultado = executar_resumos(
            ctx,
            _Painel(),
            [],
            inferencia=inferencia,
            ticker="ALZR11",
        )

        assert inferencia.chamadas == ["ALZR11"]
        assert resultado.inferencia.executada is True

    def test_falha_da_inferencia_preserva_resumos(self):
        ctx = _Contexto()

        resultado = executar_resumos(
            ctx,
            _Painel(),
            [_arquivo()],
            inferencia=_InferenciaFake(erro=RuntimeError("falhou")),
            ticker="ALZR11",
        )

        assert [e for e in ctx.eventos if e[0] == "resultado"]
        assert resultado.inferencia.falhas == 1
        assert resultado.sem_texto == 0

    def test_cancelamento_na_inferencia_encerra_sem_erro_fatal(self):
        ctx = _Contexto()
        resultado = executar_resumos(
            ctx,
            _Painel(),
            [_arquivo()],
            inferencia=_InferenciaFake(erro=OperacaoCancelada()),
            ticker="ALZR11",
        )

        assert resultado.inferencia.cancelada is True

    def test_sem_inferencia_mantem_desfecho(self):
        resultado = executar_resumos(_Contexto(), _Painel(), [_arquivo()])
        assert resultado.inferencia == ResultadoInferencia()
