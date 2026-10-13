"""Testes headless do fluxo de texto/resumo dos documentos (mixin).

Exercitam ``preparar_texto``/``_texto_cacheado`` sem instanciar Tk: o cache de
texto, a conversão em caso de *miss* e a gravação do marcador de ausência.
Resultados não definitivos (parcial, falha ou protegido) não são persistidos
nem memoizados, permitindo a retentativa automática.
"""

import logging
from pathlib import Path

from flowscope.application.document_preview import (
    SEM_TEXTO,
    ExtracaoTexto,
    StatusExtracao,
)
from flowscope.application.extracao_orcada import EXTRACAO_TIMEOUT_S
from flowscope.domain.documents import DocumentoArquivo
from flowscope.presentation.gui.charts.document_flow_mixin import DocumentFlowMixin


def _arquivo() -> DocumentoArquivo:
    return DocumentoArquivo(
        ticker="ALZR11",
        ano=2026,
        mes=2,
        categoria="Aviso aos Acionistas",
        nome="10.pdf",
        tipo="pdf",
        caminho=Path("/tmp/10.pdf"),
    )


class _SummaryFake:
    def __init__(self) -> None:
        self.persistidos: list[tuple] = []

    def chave(self, arquivo: DocumentoArquivo) -> str:
        return f"{arquivo.ticker}/{arquivo.nome}"

    def persistir(self, arquivo, resumo):
        self.persistidos.append((arquivo, resumo))
        return arquivo


class _StoreFake:
    def __init__(self) -> None:
        self.dados: dict[tuple[str, str], str] = {}
        self.salvos: list[tuple[str, str, str]] = []

    def obter(self, ticker: str, chave: str) -> str | None:
        return self.dados.get((ticker, chave))

    def salvar(self, ticker: str, chave: str, texto: str) -> None:
        self.dados[(ticker, chave)] = texto
        self.salvos.append((ticker, chave, texto))


class _FlowHost(DocumentFlowMixin):
    """Host headless que substitui a extração do arquivo por um fake."""

    def __init__(
        self, store: _StoreFake, resultado: ExtracaoTexto | None = None
    ) -> None:
        self._text_store = store
        self._summary = _SummaryFake()
        self._preview_cache: dict[Path, str] = {}
        self._resultado = resultado or ExtracaoTexto("extraído", StatusExtracao.OK)
        self.chamadas: list[Path] = []

    def _texto_do_arquivo(self, arquivo, senha=None) -> ExtracaoTexto:
        self.chamadas.append(arquivo.caminho)
        return self._resultado


class TestPrepararTexto:
    def test_miss_converte_e_grava_no_cache(self):
        store = _StoreFake()
        host = _FlowHost(store)
        arquivo = _arquivo()

        resultado = host.preparar_texto(arquivo)
        assert resultado.texto == "extraído"
        assert resultado.status is StatusExtracao.OK
        assert host.chamadas == [arquivo.caminho]
        assert store.obter("ALZR11", "ALZR11/10.pdf") == "extraído"
        assert host._preview_cache[arquivo.caminho] == "extraído"

    def test_miss_sem_texto_grava_marcador(self):
        store = _StoreFake()
        host = _FlowHost(
            store, ExtracaoTexto("", StatusExtracao.SEM_TEXTO)
        )
        arquivo = _arquivo()

        assert host.preparar_texto(arquivo).texto == ""
        assert store.obter("ALZR11", "ALZR11/10.pdf") == SEM_TEXTO

    def test_hit_usa_cache_sem_converter(self):
        store = _StoreFake()
        store.salvar("ALZR11", "ALZR11/10.pdf", "do cache")
        host = _FlowHost(store)
        arquivo = _arquivo()

        assert host.preparar_texto(arquivo).texto == "do cache"
        assert host.chamadas == []

    def test_marcador_em_cache_nao_reconverte(self):
        store = _StoreFake()
        store.salvar("ALZR11", "ALZR11/10.pdf", SEM_TEXTO)
        store.salvos.clear()
        host = _FlowHost(store)
        arquivo = _arquivo()

        assert host.preparar_texto(arquivo).texto == SEM_TEXTO
        assert host.chamadas == []
        assert store.salvos == []

    def test_parcial_nao_e_persistido_nem_memoizado(self):
        store = _StoreFake()
        host = _FlowHost(
            store, ExtracaoTexto("meio texto", StatusExtracao.PARCIAL, 1)
        )
        arquivo = _arquivo()

        resultado = host.preparar_texto(arquivo)
        assert resultado.status is StatusExtracao.PARCIAL
        assert resultado.texto == "meio texto"
        assert store.salvos == []
        assert arquivo.caminho not in host._preview_cache

    def test_falha_nao_e_persistida_nem_memoizada(self):
        store = _StoreFake()
        host = _FlowHost(store, ExtracaoTexto("", StatusExtracao.FALHA))
        arquivo = _arquivo()

        assert host.preparar_texto(arquivo).status is StatusExtracao.FALHA
        assert store.salvos == []
        assert arquivo.caminho not in host._preview_cache

    def test_protegido_nao_e_persistido_nem_memoizado(self):
        store = _StoreFake()
        host = _FlowHost(store, ExtracaoTexto("", StatusExtracao.PROTEGIDO))
        arquivo = _arquivo()

        assert host.preparar_texto(arquivo).status is StatusExtracao.PROTEGIDO
        assert store.salvos == []
        assert arquivo.caminho not in host._preview_cache


class TestTextoDefinitivo:
    def test_parcial_grava_texto_com_nota(self):
        store = _StoreFake()
        host = _FlowHost(store)
        arquivo = _arquivo()

        texto = host.persistir_texto_definitivo(
            arquivo, StatusExtracao.PARCIAL, "corpo parcial", 1
        )

        assert texto.startswith("corpo parcial")
        assert store.obter("ALZR11", "ALZR11/10.pdf") == texto
        assert host._preview_cache[arquivo.caminho] == texto

    def test_falha_grava_apenas_a_nota(self):
        store = _StoreFake()
        host = _FlowHost(store)
        arquivo = _arquivo()

        texto = host.persistir_texto_definitivo(
            arquivo, StatusExtracao.FALHA, ""
        )

        assert "erro crítico" in texto.lower()
        assert store.obter("ALZR11", "ALZR11/10.pdf") == texto

    def test_protegido_grava_apenas_a_nota(self):
        store = _StoreFake()
        host = _FlowHost(store)
        arquivo = _arquivo()

        texto = host.persistir_texto_definitivo(
            arquivo, StatusExtracao.PROTEGIDO, ""
        )

        assert "senha" in texto.lower()
        assert store.obter("ALZR11", "ALZR11/10.pdf") == texto

    def test_persistir_resumo_definitivo_delega_ao_servico(self):
        store = _StoreFake()
        host = _FlowHost(store)
        arquivo = _arquivo()
        resumo = object()

        host.persistir_resumo_definitivo(arquivo, resumo)

        assert host._summary.persistidos == [(arquivo, resumo)]


class TestTimeoutExtracao:
    def test_padrao_e_o_orcamento_do_modulo(self):
        host = DocumentFlowMixin()

        assert host.timeout_extracao() == EXTRACAO_TIMEOUT_S

    def test_definir_ajusta_apenas_em_memoria(self):
        host = DocumentFlowMixin()

        host.definir_timeout_extracao(117.0)

        assert host.timeout_extracao() == 117.0


class TestAvisosDeExtracao:
    def test_parcial_registra_warning(self, caplog):
        store = _StoreFake()
        host = _FlowHost(
            store, ExtracaoTexto("meio texto", StatusExtracao.PARCIAL, 2)
        )

        with caplog.at_level(logging.WARNING, logger="flowscope"):
            host.preparar_texto(_arquivo())

        assert (
            "Extração parcial (2 página(s) com falha): ALZR11/10.pdf"
            in caplog.text
        )

    def test_sem_texto_registra_warning(self, caplog):
        store = _StoreFake()
        host = _FlowHost(store, ExtracaoTexto("", StatusExtracao.SEM_TEXTO))

        with caplog.at_level(logging.WARNING, logger="flowscope"):
            host.preparar_texto(_arquivo())

        assert "Documento sem texto extraível: ALZR11/10.pdf" in caplog.text

    def test_cache_hit_nao_registra_aviso(self, caplog):
        store = _StoreFake()
        store.salvar("ALZR11", "ALZR11/10.pdf", "do cache")
        host = _FlowHost(store)

        with caplog.at_level(logging.WARNING, logger="flowscope"):
            host.preparar_texto(_arquivo())

        texto = caplog.text.lower()
        assert "parcial" not in texto
        assert "sem texto" not in texto

    def test_falha_registra_warning(self, caplog):
        host = _FlowHost(_StoreFake(), ExtracaoTexto("", StatusExtracao.FALHA))

        with caplog.at_level(logging.WARNING, logger="flowscope"):
            host.preparar_texto(_arquivo())

        assert "Falha crítica de extração: ALZR11/10.pdf" in caplog.text

    def test_protegido_nao_registra_aviso(self, caplog):
        host = _FlowHost(_StoreFake(), ExtracaoTexto("", StatusExtracao.PROTEGIDO))

        with caplog.at_level(logging.WARNING, logger="flowscope"):
            host.preparar_texto(_arquivo())

        texto = caplog.text.lower()
        assert "parcial" not in texto
        assert "sem texto" not in texto
