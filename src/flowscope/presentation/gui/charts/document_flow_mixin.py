"""Fluxo de pré-visualização e resumo dos documentos do painel.

Concentra a extração de texto, a geração de resumo e a composição da
pré-visualização, além da fachada usada pelo job de resumo em lote. Vive
separado de :mod:`document_tree_panel` para manter a complexidade e o tamanho
de cada módulo sob controle.
"""

import logging
import queue
import threading
import tkinter as tk

from flowscope.application.resumo_documento import ResumoDocumento
from flowscope.domain.documents import DocumentoArquivo
from flowscope.presentation.gui.charts.document_grouping import (
    Agrupamento,
    render_grupo,
)
from flowscope.presentation.gui.charts.document_preview import (
    SEM_TEXTO,
    tem_texto,
    texto_preview,
)

logger = logging.getLogger("flowscope")

#: Texto exibido enquanto a pré-visualização é extraída em segundo plano.
CARREGANDO = "Carregando…"

#: Texto exibido enquanto o resumo é gerado em segundo plano.
GERANDO_RESUMO = "Gerando resumo…"


class DocumentFlowMixin:
    """Extrai texto, gera resumo e compõe a pré-visualização do documento."""

    def documentos_sem_resumo(
        self: "DocumentFlowMixin",
    ) -> list[DocumentoArquivo]:
        """Retorna os documentos sem ``long_summary``, na ordem da árvore."""
        return [
            arquivo
            for arquivo in self._itens.values()
            if arquivo.long_summary is None
        ]

    def refresh_resumir_button(self: "DocumentFlowMixin") -> None:
        """Reavalia o estado do botão "Resumir pendentes"."""
        em_andamento = (
            self._resumir_ativo_callback() if self._resumir_ativo_callback else False
        )
        habilitado = (
            not em_andamento
            and self._summary.disponivel()
            and bool(self.documentos_sem_resumo())
        )
        self._resumir_btn.config(
            state=tk.NORMAL if habilitado else tk.DISABLED
        )

    def _mostrar_grupo(self: "DocumentFlowMixin", grupo: Agrupamento) -> None:
        """Renderiza a lista Markdown do agrupamento selecionado."""
        if self._catalogo_atual is None:
            return
        texto = render_grupo(
            self._catalogo_atual,
            grupo,
            self._por_caminho,
            self._summary.mensagem_indisponivel(),
        )
        self._set_preview_text(texto)

    def _agendar_preview(
        self: "DocumentFlowMixin", arquivo: DocumentoArquivo
    ) -> None:
        """Agenda a extração com debounce, cancelando a anterior."""
        if self._after_id is not None:
            try:
                self.frame.after_cancel(self._after_id)
            except tk.TclError:
                pass
        self._after_id = self.frame.after(
            self._debounce_ms, lambda: self._iniciar_preview(arquivo)
        )

    def _texto_cacheado(
        self: "DocumentFlowMixin", arquivo: DocumentoArquivo
    ) -> str | None:
        """Retorna o texto do documento do memo de sessão ou do cache persistente."""
        texto = self._preview_cache.get(arquivo.caminho)
        if texto is not None:
            return texto
        texto = self._text_store.obter(arquivo.ticker, self._summary.chave(arquivo))
        if texto is not None:
            self._preview_cache[arquivo.caminho] = texto
        return texto

    def _texto_do_arquivo(
        self: "DocumentFlowMixin", arquivo: DocumentoArquivo
    ) -> str:
        """Extrai o texto do arquivo; subclasses podem restringir a extração."""
        return texto_preview(arquivo.caminho)

    def preparar_texto(
        self: "DocumentFlowMixin", arquivo: DocumentoArquivo
    ) -> str:
        """Retorna o texto do documento, convertendo e gravando só em *miss*.

        Não toca em widgets: é seguro para uso na thread do job de lote.
        """
        texto = self._texto_cacheado(arquivo)
        if texto is not None:
            return texto
        texto = self._texto_do_arquivo(arquivo)
        self._text_store.salvar(
            arquivo.ticker, self._summary.chave(arquivo), texto or SEM_TEXTO
        )
        self._preview_cache[arquivo.caminho] = texto
        return texto

    def gerar_resumo_estrito(
        self: "DocumentFlowMixin", arquivo: DocumentoArquivo, texto: str
    ) -> ResumoDocumento | None:
        """Gera o resumo propagando falhas (usado pelo lote)."""
        return self._summary.gerar_estrito(arquivo, texto)

    def persistir_no_lote(self: "DocumentFlowMixin") -> bool:
        """Indica se o lote deve gravar o resumo na própria thread de trabalho.

        O padrão é ``False``; painéis que querem sobreviver a interrupções do
        lote — cancelamento, fechamento ou falha — sobrescrevem para ``True``.
        """
        return False

    def gerar_e_persistir(
        self: "DocumentFlowMixin", arquivo: DocumentoArquivo, texto: str
    ) -> ResumoDocumento | None:
        """Gera o resumo e o grava no store, sem tocar em widgets nem memória.

        É seguro chamar da thread de trabalho do lote: a orquestração de gerar
        e gravar vive no serviço de aplicação. A reflexão na árvore e na
        pré-visualização fica a cargo da thread do Tk, via
        :meth:`refletir_resumo`.
        """
        return self._summary.gerar_e_persistir(arquivo, texto)

    def _iniciar_preview(
        self: "DocumentFlowMixin", arquivo: DocumentoArquivo
    ) -> None:
        """Exibe o estado de carregamento e inicia extração/resumo em thread."""
        self._after_id = None
        req = self._req_id
        texto = self._texto_cacheado(arquivo)
        if (
            texto is not None
            and not self._summary.precisa_resumo(arquivo, texto)
            and not self._precisa_guidance(arquivo)
        ):
            self._mostrar_documento(
                texto, self._summary.resumo_para_exibir(arquivo, texto)
            )
            return
        precisa = self._summary.precisa_resumo(arquivo, texto)
        self._set_preview_text(GERANDO_RESUMO if precisa else CARREGANDO)
        fila: queue.Queue = queue.Queue()
        self._fila = fila
        threading.Thread(
            target=self._trabalhar,
            args=(arquivo, fila, texto),
            daemon=True,
        ).start()
        self._agendar_poll(arquivo, fila, req)

    def _trabalhar(
        self: "DocumentFlowMixin",
        arquivo: DocumentoArquivo,
        fila: queue.Queue,
        texto_conhecido: str | None,
    ) -> None:
        """Extrai o texto, avalia o guidance e, se preciso, gera o resumo."""
        texto = (
            texto_conhecido
            if texto_conhecido is not None
            else self.preparar_texto(arquivo)
        )
        self.avaliar_guidance(arquivo, texto)
        resumo = self._summary.gerar(arquivo, texto)
        fila.put((texto, resumo))

    def _precisa_guidance(
        self: "DocumentFlowMixin", arquivo: DocumentoArquivo
    ) -> bool:
        """Indica se um documento deve disparar avaliação de guidance."""
        servico = getattr(self, "_guidance", None)
        if servico is None:
            return False
        try:
            return servico.precisa(arquivo)
        except Exception:  # cache ilegível não deve bloquear a pré-visualização
            logger.warning(
                "Falha ao consultar guidance de %s", arquivo.caminho, exc_info=True
            )
            return False

    def avaliar_guidance(
        self: "DocumentFlowMixin", arquivo: DocumentoArquivo, texto: str | None
    ) -> None:
        """Avalia o guidance do documento, tolerando falhas.

        Aplica o gatilho de categoria, data e texto extraível por meio do
        serviço de guidance; é seguro chamar fora da thread do Tk e a partir do
        processamento em lote.
        """
        servico = getattr(self, "_guidance", None)
        if servico is None:
            return
        try:
            servico.avaliar(arquivo, texto)
        except Exception:  # falha de avaliação não deve derrubar a thread
            logger.warning(
                "Falha ao avaliar guidance de %s", arquivo.caminho, exc_info=True
            )

    def _agendar_poll(
        self: "DocumentFlowMixin",
        arquivo: DocumentoArquivo,
        fila: queue.Queue,
        req: int,
    ) -> None:
        """Consome a fila na thread do Tk até o resultado estar disponível."""

        def _verificar() -> None:
            try:
                texto, resumo = fila.get_nowait()
            except queue.Empty:
                self.frame.after(20, _verificar)
                return
            if req != self._req_id:
                return
            self._aplicar_preview(arquivo, texto, resumo)

        self.frame.after(0, _verificar)

    def _aplicar_preview(
        self: "DocumentFlowMixin",
        arquivo: DocumentoArquivo,
        texto: str,
        resumo: ResumoDocumento | None = None,
    ) -> None:
        """Cacheia o texto e exibe a pré-visualização se o arquivo seguir selecionado."""
        self._preview_cache[arquivo.caminho] = texto
        if self._arquivo_selecionado() is not arquivo:
            return
        long_summary = self._summary.resumo_para_exibir(arquivo, texto)
        if resumo is not None:
            self._atualizar_resumo(self._summary.persistir(arquivo, resumo))
            long_summary = resumo.long_summary
        self._mostrar_documento(texto, long_summary)

    def _atualizar_resumo(
        self: "DocumentFlowMixin", atualizado: DocumentoArquivo
    ) -> None:
        """Atualiza o catálogo em memória com os resumos recém-gerados."""
        for no, item in self._itens.items():
            if item.caminho == atualizado.caminho:
                self._itens[no] = atualizado
        self._por_caminho[atualizado.caminho] = atualizado
        self.refresh_resumir_button()

    def aplicar_resumo(
        self: "DocumentFlowMixin",
        arquivo: DocumentoArquivo,
        resumo: ResumoDocumento,
    ) -> None:
        """Grava o resumo e reflete-o no catálogo e na pré-visualização."""
        atualizado = self._summary.persistir(arquivo, resumo)
        self._refletir_resumo(arquivo, resumo, atualizado)

    def refletir_resumo(
        self: "DocumentFlowMixin",
        arquivo: DocumentoArquivo,
        resumo: ResumoDocumento,
    ) -> None:
        """Reflete um resumo já persistido, sem regravar no store.

        Usado pela thread do Tk quando a gravação ocorreu no worker do lote.
        """
        self._refletir_resumo(arquivo, resumo, self._summary.atualizar(arquivo, resumo))

    def _refletir_resumo(
        self: "DocumentFlowMixin",
        arquivo: DocumentoArquivo,
        resumo: ResumoDocumento,
        atualizado: DocumentoArquivo,
    ) -> None:
        """Atualiza o catálogo em memória e recompõe a pré-visualização."""
        self._atualizar_resumo(atualizado)
        selecionado = self._arquivo_selecionado()
        if selecionado is not None and selecionado.caminho == arquivo.caminho:
            texto = self._texto_cacheado(arquivo) or ""
            self._mostrar_documento(texto, resumo.long_summary)

    def _mostrar_documento(
        self: "DocumentFlowMixin", texto: str, long_summary: str | None
    ) -> None:
        """Compõe a pré-visualização do documento com o resumo longo."""
        corpo = texto if tem_texto(texto) else SEM_TEXTO
        if long_summary:
            self._set_preview_text(f"{long_summary}\n\n---\n\n{corpo}")
        else:
            self._set_preview_text(corpo)

    def _set_preview_text(self: "DocumentFlowMixin", texto: str) -> None:
        """Substitui o conteúdo da caixa de pré-visualização somente-leitura."""
        self._preview.delete("1.0", tk.END)
        self._preview.insert("1.0", texto)
