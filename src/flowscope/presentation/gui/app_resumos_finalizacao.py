"""Orquestração da finalização definitiva dos itens não conclusivos.

Submete o job de finalização ao gerenciador de background, reflete o desfecho
no painel de origem e pré-coleta as senhas dos itens protegidos. Também escala
em memória os timeouts correntes a cada reprocessamento confirmado. Vive
separado de :mod:`app_resumos_actions` para manter a complexidade e o tamanho de
cada módulo sob controle.
"""

import logging
from pathlib import Path

from flowscope.application.document_preview import StatusExtracao
from flowscope.presentation.gui.background.events import Erro
from flowscope.presentation.gui.charts.document_flow_mixin import (
    MAX_TENTATIVAS_SENHA,
)
from flowscope.presentation.gui.finalizacao_job import executar_finalizacao
from flowscope.presentation.gui.llm.mensagens import mensagem_erro_llm
from flowscope.presentation.gui.resumos_job import GRUPO, POLITICA

logger = logging.getLogger("flowscope")

#: Fator de crescimento, em memória, dos timeouts a cada retry confirmado.
FATOR_TIMEOUT_RETRY = 1.3


class ResumosFinalizacaoMixin:
    """Finalização definitiva, pré-coleta de senha e escala de timeout."""

    def _escalar_timeout(self: "ResumosFinalizacaoMixin") -> None:
        """Aumenta em 30% os timeouts correntes, apenas em memória.

        Sempre relativo ao valor em memória anterior: o orçamento de extração do
        painel e o limite de inatividade do gerenciador crescem juntos, de modo
        que o watchdog não encerre a extração antes do novo orçamento. Nada é
        persistido nem registrado como definitivo.
        """
        painel = self._painel_resumos()
        if painel is not None:
            medir = getattr(painel, "timeout_extracao", None)
            definir = getattr(painel, "definir_timeout_extracao", None)
            atual = medir() if callable(medir) else None
            if isinstance(atual, (int, float)) and callable(definir):
                definir(float(atual) * FATOR_TIMEOUT_RETRY)
        background = getattr(self, "_background", None)
        if background is not None:
            limite = getattr(background, "limite_inatividade_s", None)
            definir_limite = getattr(
                background, "definir_limite_inatividade", None
            )
            if isinstance(limite, (int, float)) and callable(definir_limite):
                definir_limite(limite * FATOR_TIMEOUT_RETRY)

    def _pre_coletar_senhas(
        self: "ResumosFinalizacaoMixin", painel: object, itens: list
    ) -> dict[Path, str]:
        """Pré-coleta as senhas dos itens protegidos, com limite de tentativas."""
        protegidos = [
            item for item in itens if item.status is StatusExtracao.PROTEGIDO
        ]
        if not protegidos:
            return {}
        solicitar = getattr(painel, "_solicitar_senha", None)
        if not callable(solicitar):
            return {}
        metodo_limite = getattr(painel, "_max_tentativas", None)
        limite = (
            int(metodo_limite())
            if callable(metodo_limite)
            else MAX_TENTATIVAS_SENHA
        )
        senhas: dict[Path, str] = {}
        for item in protegidos:
            senha = self._coletar_senha_item(solicitar, item.arquivo, limite)
            if senha:
                senhas[item.arquivo.caminho] = senha
        return senhas

    @staticmethod
    def _coletar_senha_item(
        solicitar: object, arquivo: object, limite: int
    ) -> str | None:
        """Pede a senha do item até o limite, devolvendo-a quando informada."""
        for _ in range(max(1, limite)):
            senha = solicitar(arquivo)
            if senha:
                return senha
        return None

    def _submeter_finalizacao(
        self: "ResumosFinalizacaoMixin", itens: list, guarda: object
    ) -> None:
        """Submete o job de finalização definitiva dos itens não conclusivos."""
        background = getattr(self, "_background", None)
        painel = self._painel_resumos()
        if background is None or painel is None:
            return
        self._resumos_painel = painel
        self._set_status(f"Finalizando {len(itens)} item(ns)…")

        def trabalho(ctx: object) -> None:
            executar_finalizacao(ctx, painel, itens)

        background.submit(
            trabalho,
            grupo=GRUPO,
            politica=POLITICA,
            cancelavel=True,
            ao_erro=self._registrar_erro_finalizacao,
            ao_termino=lambda evento: self._finalizar_finalizacao(),
        )

    def _registrar_erro_finalizacao(
        self: "ResumosFinalizacaoMixin", evento: Erro
    ) -> None:
        """Registra e reporta uma falha por item da finalização."""
        logger.error(
            "Falha na finalização de extração em %s: %s",
            getattr(evento.dados, "caminho", evento.dados),
            evento.excecao,
            exc_info=evento.excecao,
        )
        self._set_status(
            f"Falha ao finalizar: {mensagem_erro_llm(evento.excecao)}", "⚠"
        )

    def _finalizar_finalizacao(self: "ResumosFinalizacaoMixin") -> None:
        """Remonta o painel de origem e informa o desfecho da finalização."""
        self.after(0, self._recarregar_painel_resumos)
        painel = self._painel_resumos()
        if painel is not None:
            painel.refresh_resumir_button()
        self._flash_status("Extração finalizada como definitiva.", "✓")
