"""Testes do job de resumo em lote dos documentos pendentes."""

from pathlib import Path

from flowscope.application.resumo_documento import ResumoDocumento
from flowscope.infrastructure.document_catalog import DocumentoArquivo
from flowscope.presentation.gui.resumos_job import (
    FASE_PREPARAR,
    FASE_RESUMIR,
    MENSAGEM_ERRO,
    MENSAGEM_PROGRESSO,
    MENSAGEM_RESULTADO,
    ResumosPendentesJob,
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
    def __init__(self, textos, falha_preparar=None, falha_resumir=None):
        self._textos = textos
        self._falha_preparar = falha_preparar
        self._falha_resumir = falha_resumir
        self.preparados: list[str] = []
        self.gerados: list[str] = []

    def preparar_texto(self, arquivo):
        if self._falha_preparar == arquivo.nome:
            raise RuntimeError("conversão falhou")
        self.preparados.append(arquivo.nome)
        return self._textos.get(arquivo.nome, "")

    def gerar_resumo_estrito(self, arquivo, texto):
        if self._falha_resumir == arquivo.nome:
            raise RuntimeError("llm falhou")
        self.gerados.append(arquivo.nome)
        return ResumoDocumento("curto", "longo")


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
