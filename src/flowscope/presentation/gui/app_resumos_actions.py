"""Orquestração do resumo em lote dos documentos e notícias pendentes.

O mixin submete o lote ao gerenciador de background, traduz o progresso para a
barra de status e aplica os resultados no painel de origem. Vive separado de
:mod:`app_actions` para manter a complexidade e o tamanho de cada módulo sob
controle.
"""

import logging
import time
from pathlib import Path
from tkinter import messagebox

from flowscope.application.finalizacao_extracao import MOTIVOS_FINALIZAVEIS
from flowscope.domain.llm import LLMRateLimitError
from flowscope.presentation.gui.app_resumos_finalizacao import (
    ResumosFinalizacaoMixin,
)
from flowscope.presentation.gui.background.events import (
    Erro,
    Outcome,
    Progresso,
    Resultado,
)
from flowscope.presentation.gui.llm.mensagens import mensagem_erro_llm
from flowscope.presentation.gui.progress import ProgressReporter
from flowscope.presentation.gui.resumos_job import (
    GRUPO,
    POLITICA,
    ResultadoResumos,
    executar_resumos,
)

logger = logging.getLogger("flowscope")


class ResumosActionsMixin(ResumosFinalizacaoMixin):
    """Conduz o resumo em lote dos documentos e das notícias pendentes."""

    def _resumos_em_andamento(self: "ResumosActionsMixin") -> bool:
        """Indica se há um resumo em lote em andamento."""
        background = getattr(self, "_background", None)
        return background is not None and background.tem_ativo(GRUPO)

    def _noticias_resumos_em_andamento(self: "ResumosActionsMixin") -> bool:
        """Indica se há um resumo em lote em andamento (notícias)."""
        return self._resumos_em_andamento()

    def _resumir_documentos_pendentes(self: "ResumosActionsMixin") -> None:
        """Gera em lote os resumos dos documentos pendentes do ticker."""
        painel = getattr(self, "_documents_panel", None)
        if painel is None:
            return
        if self._resumos_em_andamento():
            return
        sem_resumo = painel.documentos_sem_resumo()
        pendentes_guidance = getattr(
            painel, "documentos_pendentes_guidance", list
        )()
        pendentes = list(sem_resumo) + list(pendentes_guidance)
        if not pendentes and not self._inferencia_pendente(painel):
            painel.refresh_resumir_button()
            return
        self._iniciar_lote_resumos(painel, pendentes, self._ticker_apresentado())

    def _caso_inferencia(self: "ResumosActionsMixin") -> object | None:
        """Retorna o caso de uso de inferência injetado, quando houver."""
        adaptadores = getattr(self, "_renda_fixa_adapters", None)
        return getattr(adaptadores, "inferencia", None)

    def _inferencia_pendente(self: "ResumosActionsMixin", painel: object) -> bool:
        """Indica se o painel encontrou inferência elegível pendente."""
        if self._caso_inferencia() is None:
            return False
        metodo = getattr(painel, "inferencia_pendente", None)
        if not callable(metodo):
            return False
        try:
            return bool(metodo())
        except Exception:
            return False

    def _resumir_noticias_pendentes(self: "ResumosActionsMixin") -> None:
        """Gera em lote os resumos das notícias pendentes do período."""
        painel = getattr(self, "_noticias_panel", None)
        if painel is None:
            return
        if self._resumos_em_andamento():
            return
        pendentes = painel.pendentes_ordenados()
        if not pendentes:
            painel.refresh_resumir_button()
            return
        self._iniciar_lote_resumos(
            painel, pendentes, self._data_referencia(), continuar=True
        )

    def _iniciar_lote_resumos(
        self: "ResumosActionsMixin",
        painel: object,
        pendentes: list,
        guarda: object,
        continuar: bool = False,
        senhas: dict[Path, str] | None = None,
    ) -> None:
        """Submete o lote de resumo e registra os callbacks de eventos."""
        background = getattr(self, "_background", None)
        if background is None:
            return
        self._resumos_painel = painel
        self._resumos_continuar = continuar
        self._resumos_falhas = 0
        self._resumos_resumidos = 0
        self._resumos_total = len(pendentes)
        self._resumos_pendentes = list(pendentes)
        self._resumos_persistir_worker = self._painel_persiste_no_worker(painel)
        self._resumos_fase = None
        self._resumos_fase_inicio = None
        self._resumos_interrompido = False
        self._resumos_cota = False
        self._resumos_reporter = ProgressReporter(
            on_update=self._presenter.on_progress
        )
        self._set_status(f"Resumindo {len(pendentes)} item(ns)…")
        estado = {"resultado": ResultadoResumos()}
        inferencia = None if continuar else self._caso_inferencia()

        def trabalho(ctx: object) -> None:
            from flowscope.presentation.composicao import bloqueio_de_escrita

            with bloqueio_de_escrita():
                estado["resultado"] = executar_resumos(
                    ctx,
                    painel,
                    pendentes,
                    continuar,
                    senhas,
                    inferencia=inferencia,
                    ticker=guarda if isinstance(guarda, str) else None,
                )

        background.submit(
            trabalho,
            grupo=GRUPO,
            politica=POLITICA,
            cancelavel=True,
            ao_progresso=self._tratar_progresso_resumos,
            ao_resultado=lambda evento: self._aplicar_resultado_resumo(
                evento, guarda
            ),
            ao_erro=self._interromper_resumos,
            ao_termino=lambda evento: self._finalizar_resumos_job(
                evento.outcome, guarda, estado["resultado"]
            ),
        )

    def _tratar_progresso_resumos(
        self: "ResumosActionsMixin", evento: Progresso
    ) -> None:
        """Traduz o progresso do lote para o relator de fases."""
        reporter = getattr(self, "_resumos_reporter", None)
        if reporter is None:
            return
        detalhe = f"{evento.atual}/{evento.total}"
        if evento.dados != getattr(self, "_resumos_fase", None):
            self._resumos_fase = evento.dados
            self._resumos_fase_inicio = time.monotonic()
            reporter.start_phase(evento.detalhe, evento.total, weight=1)
            reporter.advance(0, detalhe)
        elif evento.atual and evento.atual > 0:
            reporter.advance(1, detalhe)

    def _painel_resumos(self: "ResumosActionsMixin") -> object | None:
        """Retorna o painel de origem do lote corrente."""
        painel = getattr(self, "_resumos_painel", None)
        if painel is not None:
            return painel
        return getattr(self, "_documents_panel", None)

    def _painel_persiste_no_worker(self: "ResumosActionsMixin", painel: object) -> bool:
        """Indica se o painel grava o resumo na thread de trabalho do lote."""
        metodo = getattr(painel, "persistir_no_lote", None)
        return bool(metodo()) if metodo is not None else False

    def _aplicar_resultado_resumo(
        self: "ResumosActionsMixin", evento: Resultado, guarda: object
    ) -> None:
        """Aplica um resumo e a avaliação de guidance, descartando se o escopo mudou."""
        arquivo = evento.dados
        resumo, avaliacao = evento.valor
        if self._escopo_alterado(guarda):
            return
        painel = self._painel_resumos()
        if painel is None:
            return
        if resumo is None:
            if avaliacao is not None:
                painel.refletir_guidance(arquivo, avaliacao)
            self._contar_falha_guidance(painel, arquivo)
            return
        if getattr(self, "_resumos_persistir_worker", False):
            painel.refletir_resumo(arquivo, resumo, avaliacao)
        else:
            painel.aplicar_resumo(arquivo, resumo, avaliacao)
        self._resumos_resumidos = getattr(self, "_resumos_resumidos", 0) + 1
        self._contar_falha_guidance(painel, arquivo)

    def _contar_falha_guidance(
        self: "ResumosActionsMixin", painel: object, arquivo: object
    ) -> None:
        """Contabiliza a falha de guidance registrada para o item do lote."""
        metodo = getattr(painel, "guidance_falhou", None)
        if not callable(metodo):
            return
        try:
            falhou = metodo(arquivo)
        except Exception:  # painel sem suporte a guidance não conta falha
            return
        if falhou is True:
            self._resumos_falhas = getattr(self, "_resumos_falhas", 0) + 1

    def _interromper_resumos(self: "ResumosActionsMixin", evento: Erro) -> None:
        """Registra e reporta uma falha do lote por item.

        A cota/limite do provedor é tratada à parte: interrompe o lote, é
        registrada uma única vez (sem traceback por item) e o desfecho é
        montado em :meth:`_finalizar_resumos_job`.
        """
        arquivo = evento.dados
        exc = evento.excecao
        if isinstance(exc, LLMRateLimitError):
            self._resumos_cota = True
            logger.warning(
                "Cota da I.A. esgotada no resumo em lote; lote interrompido."
            )
            return
        if getattr(self, "_resumos_continuar", False):
            self._resumos_falhas = getattr(self, "_resumos_falhas", 0) + 1
        else:
            self._resumos_interrompido = True
        logger.error(
            "Falha no resumo em lote em %s: %s",
            arquivo.caminho,
            exc,
            exc_info=exc,
        )
        self._set_status(f"{arquivo.nome}: {mensagem_erro_llm(exc)}", "⚠")

    def _escopo_resumos(self: "ResumosActionsMixin") -> object:
        """Retorna o escopo apresentado do lote corrente (ticker ou período)."""
        if getattr(self, "_resumos_continuar", False):
            return self._data_referencia()
        return self._ticker_apresentado()

    def _escopo_alterado(self: "ResumosActionsMixin", guarda: object) -> bool:
        """Indica se o escopo apresentado mudou desde o início do lote."""
        if guarda is None:
            return False
        return guarda != self._escopo_resumos()

    def _finalizar_resumos_job(
        self: "ResumosActionsMixin",
        outcome: Outcome,
        guarda: object,
        resultado: ResultadoResumos,
    ) -> None:
        """Encerra o lote, libera o estado ocupado e exibe o desfecho.

        Cancelamento e falha fatal encerram sem confirmação. Um aborto por
        timeout/inatividade (`ABORTADO`) mantém o fluxo de reprocessamento para
        os itens já processados. O painel é remontado e o botão reavaliado em
        todos os desfechos.
        """
        self.after(0, self._recarregar_painel_resumos)
        if outcome in (Outcome.CANCELADO, Outcome.FALHA):
            self._resumos_interrompido = True
        painel = self._painel_resumos()
        if painel is not None:
            painel.refresh_resumir_button()
        if getattr(self, "_resumos_cota", False):
            total = getattr(self, "_resumos_total", 0)
            resumidos = getattr(self, "_resumos_resumidos", 0)
            self._flash_status(
                "Cota da I.A. esgotada no lote. "
                f"Resumos gerados: {resumidos} de {total}. "
                "Aguarde a renovação ou reconfigura o provedor.",
                "⚠",
            )
            return
        if getattr(self, "_resumos_interrompido", False):
            return
        if self._escopo_alterado(guarda):
            return
        if outcome is Outcome.ABORTADO:
            self._flash_status(
                "Lote encerrado por inatividade (timeout).", "⚠"
            )
            # O worker foi abortado antes de publicar a classificação; o retry
            # reconsidera o lote interrompido (itens ainda pendentes).
            self._agendar_confirmacao(
                resultado,
                guarda,
                retry=list(getattr(self, "_resumos_pendentes", [])),
            )
            return
        total = getattr(self, "_resumos_total", 0)
        resumidos = getattr(self, "_resumos_resumidos", 0)
        sem_texto = resultado.sem_texto
        if getattr(self, "_resumos_continuar", False):
            falhas = getattr(self, "_resumos_falhas", 0)
            mensagem = (
                f"Resumos gerados: {resumidos} de {total} "
                f"({sem_texto} sem texto, {falhas} falha(s))."
            )
        else:
            falhas = getattr(self, "_resumos_falhas", 0)
            complemento = f"{sem_texto} sem texto"
            if falhas:
                complemento = f"{complemento}, {falhas} falha(s)"
            mensagem = (
                f"Resumos gerados: {resumidos} de {total} ({complemento})."
            )
        self._flash_status(mensagem, "✓")
        self._agendar_confirmacao(resultado, guarda)

    def _agendar_confirmacao(
        self: "ResumosActionsMixin",
        resultado: ResultadoResumos,
        guarda: object,
        retry: list | None = None,
    ) -> None:
        """Encadeia a confirmação de finalização após a remontagem agendada."""
        definitivos = self._finalizaveis(resultado)
        if not definitivos and not retry:
            return
        self.after(
            0,
            lambda: self._confirmar_finalizacao(resultado, guarda, retry),
        )

    @staticmethod
    def _finalizaveis(resultado: ResultadoResumos) -> list:
        """Itens processados e não conclusivos elegíveis a definitivo."""
        return [
            item
            for item in resultado.nao_conclusivos
            if item.status in MOTIVOS_FINALIZAVEIS
        ]

    @staticmethod
    def _pergunta_retry(
        quantidade: int, nao_conclusiva: bool
    ) -> tuple[str, str]:
        """Monta título e texto da pergunta de reprocessamento."""
        if nao_conclusiva:
            return (
                "Extração não conclusiva",
                (
                    f"{quantidade} item(ns) de extração não conclusiva. "
                    "Deseja tentar reprocessá-los novamente?"
                ),
            )
        return (
            "Lote interrompido",
            (
                f"{quantidade} item(ns) do lote interrompido. "
                "Deseja tentar reprocessá-los novamente?"
            ),
        )

    def _confirmar_finalizacao(
        self: "ResumosActionsMixin",
        resultado: ResultadoResumos,
        guarda: object,
        retry: list | None = None,
    ) -> None:
        """Pergunta ao usuário se quer reprocessar ou finalizar os itens.

        Só é exibida com o escopo apresentado inalterado e fora de cancelamento,
        erro fatal ou cota. ``retry`` define os itens elegíveis ao
        reprocessamento (no timeout, o lote interrompido); a pergunta de
        finalização só alcança itens efetivamente processados e não conclusivos
        — pendentes nunca processados ficam fora. Recusar ambas encerra sem
        alterar os itens.
        """
        if getattr(self, "_resumos_cota", False):
            return
        if getattr(self, "_resumos_interrompido", False):
            return
        if self._escopo_alterado(guarda):
            return
        definitivos = self._finalizaveis(resultado)
        retry = self._resolver_retry(retry, definitivos)
        if not retry and not definitivos:
            return
        if retry and self._perguntar_reprocessar(retry, bool(definitivos)):
            self._reprocessar_lista(retry, definitivos, guarda)
            return
        if definitivos and self._perguntar_finalizar(len(definitivos)):
            self._submeter_finalizacao(definitivos, guarda)

    @staticmethod
    def _resolver_retry(retry: list | None, definitivos: list) -> list:
        """Resolve a lista de retry: explícita (timeout) ou os não conclusivos."""
        if retry is not None:
            return list(retry)
        return [item.arquivo for item in definitivos]

    def _perguntar_reprocessar(
        self: "ResumosActionsMixin", retry: list, nao_conclusiva: bool
    ) -> bool:
        """Pergunta se o usuário quer reprocessar a lista."""
        titulo, pergunta = self._pergunta_retry(len(retry), nao_conclusiva)
        return bool(messagebox.askyesno(titulo, pergunta, parent=self))

    def _perguntar_finalizar(
        self: "ResumosActionsMixin", quantidade: int
    ) -> bool:
        """Pergunta se o usuário quer marcar os itens como definitivos."""
        return bool(
            messagebox.askyesno(
                "Finalizar extração",
                f"Deseja marcar os {quantidade} item(ns) como definitivos? "
                "Eles sairão dos pendentes e não serão reprocessados.",
                parent=self,
            )
        )

    def _reprocessar_lista(
        self: "ResumosActionsMixin",
        arquivos: list,
        protegidos: list,
        guarda: object,
    ) -> None:
        """Reprocessa a lista, pré-coletando a senha dos protegidos.

        A pré-coleta ocorre na thread do Tk; o lote recebe um mapa
        ``{caminho: senha}`` e não solicita senha durante o processamento. Item
        protegido sem senha informada permanece pendente.
        """
        if not arquivos:
            return
        painel = self._painel_resumos()
        if painel is None:
            return
        self._escalar_timeout()
        senhas = self._pre_coletar_senhas(painel, protegidos)
        self._iniciar_lote_resumos(
            painel,
            list(arquivos),
            guarda,
            continuar=getattr(self, "_resumos_continuar", False),
            senhas=senhas,
        )

    def _recarregar_painel_resumos(self: "ResumosActionsMixin") -> None:
        """Remonta o painel de origem do lote a partir do cache atualizado.

        A remontagem é adiada para depois de o gerenciador remover o job — quando
        eventuais gravações do worker já terminaram — e reusa a leitura fora da
        thread do Tk. Notícias (lote contínuo) e documentos são despachados por
        origem.
        """
        if getattr(self, "_resumos_continuar", False):
            self._submeter_leitura_noticias(self._data_referencia())
        else:
            self._submeter_leitura_documentos(self._ticker_apresentado())
