"""Fluxo de pré-visualização e resumo dos documentos do painel.

Concentra a extração de texto, a geração de resumo e a composição da
pré-visualização, além da fachada usada pelo job de resumo em lote. Vive
separado de :mod:`document_tree_panel` para manter a complexidade e o tamanho
de cada módulo sob controle.
"""

import logging
import tkinter as tk

from flowscope.application.document_preview import (
    SEM_TEXTO,
    ExtracaoTexto,
    StatusExtracao,
    extrair_arquivo,
    tem_texto,
)
from flowscope.application.resumo_documento import ResumoDocumento
from flowscope.domain.documents import DocumentoArquivo
from flowscope.presentation.gui.background.context import JobContext
from flowscope.presentation.gui.background.job import Politica
from flowscope.presentation.gui.background.manager import BackgroundManager
from flowscope.presentation.gui.charts.document_grouping import (
    Agrupamento,
    render_grupo,
)

logger = logging.getLogger("flowscope")

#: Texto exibido enquanto a pré-visualização é extraída em segundo plano.
CARREGANDO = "Carregando…"

#: Texto exibido enquanto o resumo é gerado em segundo plano.
GERANDO_RESUMO = "Gerando resumo…"

#: Grupo de exclusão da pré-visualização de documentos.
GRUPO_PREVIEW = "preview"

#: Número máximo de tentativas de senha por documento/seleção.
MAX_TENTATIVAS_SENHA = 3


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
        self._tentativas_senha().pop(arquivo.caminho, None)
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
        self: "DocumentFlowMixin",
        arquivo: DocumentoArquivo,
        senha: str | None = None,
    ) -> ExtracaoTexto:
        """Extrai o texto do arquivo; subclasses podem restringir a extração."""
        return extrair_arquivo(arquivo.caminho, senha=senha)

    def preparar_texto(
        self: "DocumentFlowMixin",
        arquivo: DocumentoArquivo,
        senha: str | None = None,
    ) -> ExtracaoTexto:
        """Retorna o texto do documento, convertendo e gravando só em *miss*.

        Apenas resultados definitivos (completo ou ausência de texto) são
        persistidos e memoizados; resultados parciais, de falha ou protegidos
        permanecem pendentes, permitindo a retentativa automática.

        Não toca em widgets: é seguro para uso na thread do job de lote.
        """
        texto = self._texto_cacheado(arquivo)
        if texto is not None:
            status = (
                StatusExtracao.OK if tem_texto(texto) else StatusExtracao.SEM_TEXTO
            )
            return ExtracaoTexto(texto, status)
        resultado = self._texto_do_arquivo(arquivo, senha)
        if resultado.status in (StatusExtracao.OK, StatusExtracao.SEM_TEXTO):
            self._text_store.salvar(
                arquivo.ticker,
                self._summary.chave(arquivo),
                resultado.texto or SEM_TEXTO,
            )
            self._preview_cache[arquivo.caminho] = resultado.texto
        return resultado

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
        self: "DocumentFlowMixin",
        arquivo: DocumentoArquivo,
        senha: str | None = None,
    ) -> None:
        """Exibe o carregamento e inicia extração/resumo em background.

        Não lê o cache de texto nem avalia resumo/guidance na thread do Tk:
        apenas publica o estado de carregamento e submete o trabalho. A leitura
        do cache e a decisão de resumo/guidance ocorrem no worker.
        """
        self._after_id = None
        self._set_preview_text(CARREGANDO)
        self._preview_background().submit(
            lambda ctx: self._trabalhar(ctx, arquivo, senha),
            grupo=GRUPO_PREVIEW,
            politica=Politica.LATEST_WINS,
            chave=arquivo.caminho,
            ao_resultado=lambda evento: self._aplicar_preview(
                arquivo, *evento.valor
            ),
            ao_erro=lambda evento: self._falhar_preview(arquivo),
        )

    def _falhar_preview(
        self: "DocumentFlowMixin", arquivo: DocumentoArquivo
    ) -> None:
        """Sai do carregamento com mensagem informativa se o arquivo segue selecionado.

        A falha da extração ou da geração do resumo não é fatal: a caixa de
        pré-visualização exibe o vocabulário de indisponibilidade e o desfecho
        de um documento já trocado é descartado.
        """
        if self._arquivo_selecionado() is not arquivo:
            return
        self._set_preview_text(self._summary.mensagem_indisponivel())

    def _preview_background(self: "DocumentFlowMixin") -> BackgroundManager:
        """Retorna o gerenciador de background da pré-visualização."""
        gerenciador = getattr(self, "_preview_manager", None)
        if gerenciador is None:
            gerenciador = BackgroundManager(self.frame.after)
            self._preview_manager = gerenciador
        return gerenciador

    def _trabalhar(
        self: "DocumentFlowMixin",
        ctx: "JobContext",
        arquivo: DocumentoArquivo,
        senha: str | None = None,
    ) -> None:
        """Extrai o texto, avalia o guidance e, se preciso, gera o resumo.

        Executa fora da thread do Tk: lê o cache persistente de texto, decide se
        o resumo é necessário e avalia o guidance, devolvendo texto, decisão e
        resumo no resultado do job. Um resultado parcial não gera resumo,
        permanecendo pendente para nova extração.
        """
        resultado = self.preparar_texto(arquivo, senha)
        precisa = (
            resultado.status is StatusExtracao.OK
            and self._summary.precisa_resumo(arquivo, resultado.texto)
        )
        resumo = (
            self._summary.gerar(arquivo, resultado.texto) if precisa else None
        )
        if self._precisa_guidance(arquivo):
            self.avaliar_guidance(arquivo, resultado.texto, resumo)
        ctx.resultado(valor=(resultado, precisa, resumo))

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
        self: "DocumentFlowMixin",
        arquivo: DocumentoArquivo,
        texto: str | None,
        resumo: ResumoDocumento | None = None,
    ) -> None:
        """Avalia o guidance do documento, tolerando falhas.

        Aplica o gatilho de categoria e a cascata de fontes por meio do serviço
        de guidance; é seguro chamar fora da thread do Tk e a partir do
        processamento em lote.
        """
        servico = getattr(self, "_guidance", None)
        if servico is None:
            return
        try:
            servico.avaliar(arquivo, texto, resumo)
        except Exception:  # falha de avaliação não deve derrubar a thread
            logger.warning(
                "Falha ao avaliar guidance de %s", arquivo.caminho, exc_info=True
            )

    def _aplicar_preview(
        self: "DocumentFlowMixin",
        arquivo: DocumentoArquivo,
        resultado: ExtracaoTexto,
        precisa_resumo: bool,
        resumo: ResumoDocumento | None = None,
    ) -> None:
        """Cacheia o texto e exibe a pré-visualização se o arquivo seguir selecionado.

        Recebe o resultado da extração, a decisão de resumo e o resumo gerado
        pelo worker. Um PDF protegido dispara a solicitação de senha (quando
        interativo). Um documento já resumido tem ``precisa_resumo`` falso e
        reutiliza o resumo em memória; quando o resumo era necessário mas a
        geração falhou, exibe a mensagem de indisponibilidade.
        """
        if self._arquivo_selecionado() is not arquivo:
            return
        if self._tentar_senha(arquivo, resultado):
            return
        if resumo is not None:
            self._atualizar_resumo(self._summary.persistir(arquivo, resumo))
            self._mostrar_documento(resultado.texto, resumo.long_summary)
            return
        long_summary = (
            self._summary.mensagem_indisponivel()
            if precisa_resumo
            else self._summary.resumo_para_exibir(arquivo, resultado.texto)
        )
        anotacao = (
            self._anotacao_parcial(resultado.paginas_com_falha)
            if resultado.status is StatusExtracao.PARCIAL
            else None
        )
        self._mostrar_documento(resultado.texto, long_summary, anotacao)

    def _tentar_senha(
        self: "DocumentFlowMixin",
        arquivo: DocumentoArquivo,
        resultado: ExtracaoTexto,
    ) -> bool:
        """Solicita a senha de um PDF protegido e reprograma a extração.

        Retorna ``True`` quando uma nova extração foi submetida com a senha
        informada (a exibição fica a cargo desse novo resultado) e ``False``
        quando não há o que solicitar — fluxo não interativo, limite atingido ou
        usuário cancelou.
        """
        if resultado.status is not StatusExtracao.PROTEGIDO:
            return False
        if not self._pode_solicitar_senha():
            return False
        tentativas = self._tentativas_senha()
        atual = tentativas.get(arquivo.caminho, 0)
        if atual >= self._max_tentativas():
            return False
        senha = self._solicitar_senha(arquivo)
        tentativas[arquivo.caminho] = atual + 1
        if not senha:
            return False
        self._iniciar_preview(arquivo, senha)
        return True

    def _pode_solicitar_senha(self: "DocumentFlowMixin") -> bool:
        """Indica se o painel é interativo e pode pedir senha ao usuário."""
        return bool(getattr(self, "_senha_interativa", False))

    def _solicitar_senha(
        self: "DocumentFlowMixin", arquivo: DocumentoArquivo
    ) -> str | None:
        """Solicita a senha do documento; padrão headless devolve ``None``."""
        return None

    def _max_tentativas(self: "DocumentFlowMixin") -> int:
        """Retorna o limite de tentativas de senha do painel."""
        return int(getattr(self, "_senha_max_tentativas", MAX_TENTATIVAS_SENHA))

    def _tentativas_senha(self: "DocumentFlowMixin") -> dict:
        """Retorna o mapa de tentativas de senha por documento, criando-o."""
        tentativas = getattr(self, "_senha_tentativas", None)
        if tentativas is None:
            tentativas = {}
            self._senha_tentativas = tentativas
        return tentativas

    @staticmethod
    def _anotacao_parcial(paginas_com_falha: int) -> str:
        """Monta a anotação de extração parcial exibida antes do texto."""
        return (
            f"[Texto parcial: {paginas_com_falha} página(s) não pôde(ram) ser "
            "extraída(s).]"
        )

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
        self: "DocumentFlowMixin",
        texto: str,
        long_summary: str | None,
        anotacao: str | None = None,
    ) -> None:
        """Compõe a pré-visualização do documento com o resumo longo."""
        corpo = texto if tem_texto(texto) else SEM_TEXTO
        if anotacao:
            corpo = f"{anotacao}\n\n{corpo}"
        if long_summary:
            self._set_preview_text(f"{long_summary}\n\n---\n\n{corpo}")
        else:
            self._set_preview_text(corpo)

    def _set_preview_text(self: "DocumentFlowMixin", texto: str) -> None:
        """Substitui o conteúdo da caixa de pré-visualização somente-leitura."""
        self._preview.delete("1.0", tk.END)
        self._preview.insert("1.0", texto)
