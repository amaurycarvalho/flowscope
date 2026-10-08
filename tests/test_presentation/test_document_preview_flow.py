"""Testes headless do fluxo de pré-visualização de documentos.

Exercitam ``_iniciar_preview``/``_trabalhar``/``_aplicar_preview`` sem instanciar
Tk: a leitura de cache, a decisão de resumo e a composição da pré-visualização
são dirigidas por um manager fake que roda o worker sob demanda.
"""

from dataclasses import replace
from pathlib import Path

from flowscope.application.document_preview import (
    SEM_TEXTO,
    ExtracaoTexto,
    StatusExtracao,
)
from flowscope.application.documentos.document_summary import (
    DocumentSummaryService,
)
from flowscope.application.documentos.mensagens import mensagem_indisponivel
from flowscope.application.resumo_documento import ResumoDocumento
from flowscope.domain.documents import DocumentoArquivo
from flowscope.domain.llm import LLMCommunicationError, LLMResposta
from flowscope.infrastructure.document_summaries import JsonDocumentSummaryStore
from flowscope.infrastructure.document_texts import JsonDocumentTextStore
from flowscope.presentation.gui.background.context import JobContext
from flowscope.presentation.gui.background.events import Erro, Resultado
from flowscope.presentation.gui.background.job import JobHandle, Politica
from flowscope.presentation.gui.charts.document_flow_mixin import (
    CARREGANDO,
    GRUPO_PREVIEW,
    DocumentFlowMixin,
)


def _arquivo(nome: str = "10.pdf", long_summary: str | None = None) -> DocumentoArquivo:
    return DocumentoArquivo(
        ticker="ALZR11",
        ano=2026,
        mes=2,
        categoria="Aviso aos Acionistas",
        nome=nome,
        tipo="pdf",
        caminho=Path(f"/cache/{nome}"),
        long_summary=long_summary,
    )


class _StoreFake:
    def __init__(self) -> None:
        self.dados: dict[tuple[str, str], str] = {}
        self.obtidos = 0
        self.salvos: list[tuple[str, str, str]] = []

    def obter(self, ticker: str, chave: str) -> str | None:
        self.obtidos += 1
        return self.dados.get((ticker, chave))

    def salvar(self, ticker: str, chave: str, texto: str) -> None:
        self.dados[(ticker, chave)] = texto
        self.salvos.append((ticker, chave, texto))


class _SummaryFake:
    def __init__(self, disponivel: bool = True) -> None:
        self._disponivel = disponivel
        self.gerados: list[tuple[DocumentoArquivo, str]] = []
        self.resumo_a_gerar: ResumoDocumento | None = None
        self.persistidos: list[tuple[DocumentoArquivo, ResumoDocumento]] = []
        self.mensagem = "Resumo indisponível"

    def disponivel(self) -> bool:
        return self._disponivel

    def precisa_resumo(self, arquivo: DocumentoArquivo, texto: str | None) -> bool:
        return (
            arquivo.long_summary is None
            and self._disponivel
            and bool(texto and texto.strip())
        )

    def gerar(
        self, arquivo: DocumentoArquivo, texto: str
    ) -> ResumoDocumento | None:
        self.gerados.append((arquivo, texto))
        if not self.precisa_resumo(arquivo, texto):
            return None
        return self.resumo_a_gerar

    def resumo_para_exibir(
        self, arquivo: DocumentoArquivo, texto: str
    ) -> str | None:
        if arquivo.long_summary is not None:
            return arquivo.long_summary
        if texto and texto.strip():
            return self.mensagem
        return None

    def mensagem_indisponivel(self) -> str:
        return self.mensagem

    def persistir(
        self, arquivo: DocumentoArquivo, resumo: ResumoDocumento
    ) -> DocumentoArquivo:
        self.persistidos.append((arquivo, resumo))
        return replace(
            arquivo,
            short_summary=resumo.short_summary,
            long_summary=resumo.long_summary,
        )

    def chave(self, arquivo: DocumentoArquivo) -> str:
        return arquivo.nome


class _ManagerFake:
    """Captura o trabalho submetido para executá-lo sob demanda no teste."""

    def __init__(self) -> None:
        self.trabalho = None
        self.ao_resultado = None
        self.ao_erro = None
        self.grupo = None
        self.politica = None
        self.chave = None
        self.submissoes = 0

    def submit(
        self,
        trabalho,
        *,
        grupo,
        politica,
        chave=None,
        ao_resultado=None,
        ao_erro=None,
        **kwargs,
    ):
        self.trabalho = trabalho
        self.ao_resultado = ao_resultado
        self.ao_erro = ao_erro
        self.grupo = grupo
        self.politica = politica
        self.chave = chave
        self.submissoes += 1
        return JobHandle(id=1, grupo=grupo, politica=politica, chave=chave)

    def executar(self) -> None:
        eventos: list = []
        handle = JobHandle(id=1, grupo=self.grupo, politica=self.politica)
        try:
            self.trabalho(JobContext(handle, eventos.append))
        except Exception as exc:
            if self.ao_erro is not None:
                self.ao_erro(Erro(excecao=exc))
            return
        for evento in eventos:
            if isinstance(evento, Resultado) and self.ao_resultado is not None:
                self.ao_resultado(evento)


class _PreviewHost(DocumentFlowMixin):
    """Host headless que registra a exibição e a atualização do catálogo."""

    def __init__(
        self,
        *,
        store: _StoreFake | None = None,
        summary: _SummaryFake | None = None,
        convertido: str = "conteúdo do arquivo",
    ) -> None:
        self._text_store = store or _StoreFake()
        self._summary = summary or _SummaryFake()
        self._guidance = None
        self._preview_cache: dict[Path, str] = {}
        self._itens: dict[str, DocumentoArquivo] = {}
        self._por_caminho: dict[Path, DocumentoArquivo] = {}
        self._after_id = None
        self.selecionado: DocumentoArquivo | None = None
        self.convertido = convertido
        self.conversoes: list[Path] = []
        self.manager = _ManagerFake()
        self.texto_exibido: str | None = None
        self.resumos_atualizados: list[DocumentoArquivo] = []
        self.refresh = 0

    def _preview_background(self):
        return self.manager

    def _set_preview_text(self, texto: str) -> None:
        self.texto_exibido = texto

    def _arquivo_selecionado(self):
        return self.selecionado

    def _atualizar_resumo(self, atualizado: DocumentoArquivo) -> None:
        self.resumos_atualizados.append(atualizado)
        super()._atualizar_resumo(atualizado)

    def refresh_resumir_button(self) -> None:
        self.refresh += 1

    def _texto_do_arquivo(self, arquivo, senha=None) -> ExtracaoTexto:
        self.conversoes.append(arquivo.caminho)
        status = (
            StatusExtracao.OK if self.convertido else StatusExtracao.SEM_TEXTO
        )
        return ExtracaoTexto(self.convertido, status)


class TestIniciarPreview:
    def test_mostra_carregando_sem_ler_cache_na_thread(self):
        host = _PreviewHost()
        arquivo = _arquivo()
        host.selecionado = arquivo

        host._iniciar_preview(arquivo)

        assert host.texto_exibido == CARREGANDO
        assert host._text_store.obtidos == 0
        assert host._summary.gerados == []
        assert host.manager.submissoes == 1
        assert host.manager.grupo == GRUPO_PREVIEW
        assert host.manager.politica is Politica.LATEST_WINS
        assert host.manager.chave == arquivo.caminho


class TestTrabalharEAplicar:
    def test_usa_texto_do_cache_sem_converter(self):
        store = _StoreFake()
        store.dados[("ALZR11", "10.pdf")] = "do cache"
        summary = _SummaryFake(disponivel=False)
        host = _PreviewHost(store=store, summary=summary)
        arquivo = _arquivo()
        host.selecionado = arquivo

        host._iniciar_preview(arquivo)
        host.manager.executar()

        assert host.conversoes == []
        assert host.texto_exibido == (
            "Resumo indisponível\n\n---\n\ndo cache"
        )

    def test_miss_converte_grava_e_exibe(self):
        store = _StoreFake()
        summary = _SummaryFake(disponivel=False)
        host = _PreviewHost(store=store, summary=summary)
        arquivo = _arquivo()
        host.selecionado = arquivo

        host._iniciar_preview(arquivo)
        host.manager.executar()

        assert host.conversoes == [arquivo.caminho]
        assert store.obter("ALZR11", "10.pdf") == "conteúdo do arquivo"
        assert host.texto_exibido == (
            "Resumo indisponível\n\n---\n\nconteúdo do arquivo"
        )

    def test_gera_persiste_e_exibe_resumo(self):
        store = _StoreFake()
        summary = _SummaryFake()
        summary.resumo_a_gerar = ResumoDocumento("curto", "longo")
        host = _PreviewHost(store=store, summary=summary)
        arquivo = _arquivo()
        host.selecionado = arquivo

        host._iniciar_preview(arquivo)
        host.manager.executar()

        assert summary.persistidos
        assert host.resumos_atualizados
        assert host.texto_exibido == (
            "longo\n\n---\n\nconteúdo do arquivo"
        )

    def test_documento_ja_resumido_reutiliza_resumo(self):
        store = _StoreFake()
        store.dados[("ALZR11", "10.pdf")] = "corpo integral"
        summary = _SummaryFake()
        host = _PreviewHost(store=store, summary=summary)
        arquivo = _arquivo(long_summary="resumo longo")
        host.selecionado = arquivo

        host._iniciar_preview(arquivo)
        host.manager.executar()

        assert summary.gerados == []
        assert summary.persistidos == []
        assert host.texto_exibido == (
            "resumo longo\n\n---\n\ncorpo integral"
        )

    def test_sem_texto_nao_gera_resumo(self):
        store = _StoreFake()
        summary = _SummaryFake()
        host = _PreviewHost(store=store, summary=summary, convertido="")
        arquivo = _arquivo()
        host.selecionado = arquivo

        host._iniciar_preview(arquivo)
        host.manager.executar()

        assert store.salvos == [("ALZR11", "10.pdf", SEM_TEXTO)]
        assert summary.persistidos == []
        assert host.texto_exibido == SEM_TEXTO

    def test_resultado_de_arquivo_trocado_e_ignorado(self):
        store = _StoreFake()
        summary = _SummaryFake()
        host = _PreviewHost(store=store, summary=summary)
        arquivo = _arquivo()
        host.selecionado = _arquivo("20.pdf")

        host._iniciar_preview(arquivo)
        host.manager.executar()

        assert host.texto_exibido == CARREGANDO
        assert host.resumos_atualizados == []


class TestFalhaPreview:
    def _host_com_falha(self) -> _PreviewHost:
        host = _PreviewHost()

        def _falhar(arquivo, senha=None):
            raise RuntimeError("boom")

        host._texto_do_arquivo = _falhar
        return host

    def test_falha_exibe_mensagem_e_sai_do_carregamento(self):
        host = self._host_com_falha()
        arquivo = _arquivo()
        host.selecionado = arquivo

        host._iniciar_preview(arquivo)
        host.manager.executar()

        assert host.texto_exibido == host._summary.mensagem_indisponivel()

    def test_falha_de_documento_trocado_e_descartada(self):
        host = self._host_com_falha()
        arquivo = _arquivo()
        host.selecionado = _arquivo("20.pdf")

        host._iniciar_preview(arquivo)
        host.manager.executar()

        assert host.texto_exibido == CARREGANDO


class _LLMFake:
    def __init__(
        self, resposta: str = "", erro: Exception | None = None
    ) -> None:
        self.resposta = resposta
        self.erro = erro
        self.chamadas: list = []

    def complete(self, messages, system_prompt=None):
        self.chamadas.append(messages)
        if self.erro is not None:
            raise self.erro
        return LLMResposta(texto=self.resposta)


def _host_servico(
    tmp_path,
    llm,
    *,
    disponivel: bool = True,
    convertido: str = "Conteudo do informe",
) -> _PreviewHost:
    summary_store = JsonDocumentSummaryStore(cache_dir=tmp_path)
    text_store = JsonDocumentTextStore(cache_dir=tmp_path)
    service = DocumentSummaryService(
        summary_store,
        tmp_path,
        llm_factory=lambda: llm,
        llm_available=lambda: disponivel,
    )
    host = _PreviewHost(store=text_store, convertido=convertido)
    host._summary = service
    host.summary_store = summary_store
    return host


class TestGeracaoDeResumoHeadless:
    def test_preview_composta_com_resumo_longo(self, tmp_path):
        host = _host_servico(tmp_path, _LLMFake(), disponivel=False)
        host.summary_store.salvar("ALZR11", "20.html", "curto", "resumo longo")
        arquivo = _arquivo("20.html", long_summary="resumo longo")
        host.selecionado = arquivo

        host._iniciar_preview(arquivo)
        host.manager.executar()

        assert host.texto_exibido == (
            "resumo longo\n\n---\n\nConteudo do informe"
        )

    def test_gera_resumo_persiste_e_atualiza_catalogo(self, tmp_path):
        llm = _LLMFake("CURTO: curto\nLONGO: longo")
        host = _host_servico(tmp_path, llm)
        arquivo = _arquivo("20.html")
        host.selecionado = arquivo
        host._itens = {"no": arquivo}
        host._por_caminho = {arquivo.caminho: arquivo}

        host._iniciar_preview(arquivo)
        host.manager.executar()

        assert host.texto_exibido == "longo\n\n---\n\nConteudo do informe"
        assert len(llm.chamadas) == 1
        assert host._itens["no"].short_summary == "curto"
        assert host._itens["no"].long_summary == "longo"
        assert (
            host.summary_store.obter("ALZR11", "20.html").long_summary
            == "longo"
        )

    def test_sem_llm_exibe_mensagem_sem_chamar(self, tmp_path):
        llm = _LLMFake("CURTO: curto\nLONGO: longo")
        host = _host_servico(tmp_path, llm, disponivel=False)
        arquivo = _arquivo("20.html")
        host.selecionado = arquivo

        host._iniciar_preview(arquivo)
        host.manager.executar()

        assert host.texto_exibido == (
            f"{mensagem_indisponivel(False)}\n\n---\n\nConteudo do informe"
        )
        assert llm.chamadas == []
        assert host.summary_store.resumos("ALZR11") == {}

    def test_sem_texto_nao_chama_llm_nem_persiste(self, tmp_path):
        llm = _LLMFake("CURTO: curto\nLONGO: longo")
        host = _host_servico(tmp_path, llm, convertido="")
        arquivo = _arquivo("20.html")
        host.selecionado = arquivo

        host._iniciar_preview(arquivo)
        host.manager.executar()

        assert host.texto_exibido == SEM_TEXTO
        assert llm.chamadas == []
        assert host.summary_store.resumos("ALZR11") == {}

    def test_falha_tipada_exibe_mensagem(self, tmp_path):
        llm = _LLMFake(erro=LLMCommunicationError("timeout"))
        host = _host_servico(tmp_path, llm)
        arquivo = _arquivo("20.html")
        host.selecionado = arquivo

        host._iniciar_preview(arquivo)
        host.manager.executar()

        assert mensagem_indisponivel(True) in (host.texto_exibido or "")
