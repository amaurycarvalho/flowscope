"""Montagem do contexto do chat com documentos, fundamentos e fontes.

Reúne o bloco de conhecimento, os fundamentos da watchlist, a cascata de
documentos e as fontes adicionais em um ``ContextoChat``. O escalonamento para
o texto integral e o gate de confirmação por quantidade são regras de
aplicação; o diálogo de confirmação é delegado a um callback da apresentação.
"""

import logging
from collections.abc import Callable, Iterable, Mapping

from flowscope.application.chat.consultar import (
    ContextoChat,
    ContextoDocumental,
    FonteContexto,
)
from flowscope.application.chat.documentos import (
    FAIXA_AUTOMATICA,
    CascataDocumentos,
    faixa_confirmacao,
)
from flowscope.application.chat.fundamentos import montar_contexto_fundamentos

logger = logging.getLogger("flowscope")

#: Assinatura de um provedor de fonte adicional dependente da pergunta.
FonteAdicional = Callable[[str], FonteContexto | None]

#: Assinatura do callback que confirma a leitura do texto integral.
ConfirmaLeitura = Callable[[int, list[str]], bool]

#: Teto de nomes listados no diálogo de confirmação.
_MAX_NOMES_LISTADOS = 7


class MontarContextoChat:
    """Monta o ``ContextoChat`` de uma pergunta a partir das fontes de dados."""

    def __init__(
        self: "MontarContextoChat",
        cascata: CascataDocumentos,
        fontes_adicionais: Iterable[FonteAdicional] | None = None,
        confirmar: ConfirmaLeitura | None = None,
        conhecimento: str = "",
    ) -> None:
        """Guarda a cascata, as fontes adicionais e o callback de confirmação."""
        self._cascata = cascata
        self._fontes_adicionais = list(fontes_adicionais or [])
        self._confirmar = confirmar
        self._conhecimento = conhecimento

    def montar(
        self: "MontarContextoChat",
        pergunta: str,
        fundamentos: Mapping[str, object],
        watchlist: Iterable[str],
        ticker: str | None = None,
    ) -> ContextoChat:
        """Monta o contexto completo de uma pergunta do chat."""
        resumos, _alvos = self._cascata.montar_resumos(ticker, watchlist)
        documental = ContextoDocumental(
            resumos=resumos,
            preparar_texto=self.preparar_texto,
            confirmar=self.confirmar_leitura,
        )
        return ContextoChat(
            conhecimento=self._conhecimento,
            fundamentos=montar_contexto_fundamentos(fundamentos, ticker, watchlist),
            documentos=documental,
            fontes_adicionais=self.preparar_fontes_adicionais(pergunta),
        )

    def preparar_fontes_adicionais(
        self: "MontarContextoChat", pergunta: str
    ) -> list[FonteContexto]:
        """Coleta as fontes adicionais, omitindo as que falham ou vêm vazias."""
        fontes: list[FonteContexto] = []
        for provider in self._fontes_adicionais:
            try:
                fonte = provider(pergunta)
            except Exception:
                logger.warning(
                    "Fonte adicional de contexto falhou; ignorando.", exc_info=True
                )
                continue
            if fonte is not None and fonte.texto:
                fontes.append(fonte)
        return fontes

    def preparar_texto(self: "MontarContextoChat", chaves: list[str]) -> str:
        """Resolve as chaves nos documentos e nas fontes adicionais escaláveis."""
        restantes = set(chaves)
        partes: list[str] = []
        docs = self._cascata.resolver_alvos(chaves)
        if docs:
            partes.append(self._cascata.preparar_texto(docs))
            restantes -= {doc.chave for doc in docs}
        for fonte in self._fontes_escalaveis():
            alvos = fonte.resolver_alvos(restantes)
            if not alvos:
                continue
            partes.append(fonte.preparar_texto(alvos))
            restantes -= {alvo.chave for alvo in alvos}
        return "\n\n".join(parte for parte in partes if parte)

    def confirmar_leitura(self: "MontarContextoChat", chaves: list[str]) -> bool:
        """Aplica o gate de confirmação somando documentos e fontes adicionais."""
        nomes = [doc.nome for doc in self._cascata.resolver_alvos(chaves)]
        for fonte in self._fontes_escalaveis():
            nomes.extend(alvo.nome for alvo in fonte.resolver_alvos(chaves))
        if faixa_confirmacao(len(nomes)) == FAIXA_AUTOMATICA:
            return True
        if self._confirmar is None:
            return True
        return bool(
            self._confirmar(
                len(nomes),
                nomes if len(nomes) <= _MAX_NOMES_LISTADOS else [],
            )
        )

    def _fontes_escalaveis(self: "MontarContextoChat") -> list[object]:
        """Fontes adicionais que resolvem chaves para o conteúdo integral.

        A fonte de notícias expõe ``resolver_alvos``/``preparar_texto``; fontes
        que não implementam o escalonamento (apenas texto) são ignoradas aqui.
        """
        return [
            fonte
            for fonte in self._fontes_adicionais
            if callable(getattr(fonte, "resolver_alvos", None))
            and callable(getattr(fonte, "preparar_texto", None))
        ]
