"""Montagem do contexto do chat com documentos, fundamentos e fontes.

Reúne o bloco de conhecimento, os fundamentos da watchlist, a cascata de
documentos e as fontes adicionais em um ``ContextoChat``. O escalonamento para
o texto integral e o gate de confirmação por quantidade são regras de
aplicação; o diálogo de confirmação é delegado a um callback da apresentação.
"""

import hashlib
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


def assinatura_bloco(conhecimento: str, fundamentos: str, resumos: str) -> str:
    """Deriva a assinatura determinística do bloco estável a partir do conteúdo."""
    digest = hashlib.sha256()
    for parte in (conhecimento, fundamentos, resumos):
        digest.update(parte.encode("utf-8"))
        digest.update(b"\x00")
    return digest.hexdigest()


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
        cache: tuple[str, str] | None = None,
    ) -> ContextoChat:
        """Monta o contexto completo de uma pergunta do chat.

        ``cache`` é o último ``(assinatura, bloco)`` memoizado; quando a
        assinatura coincide, o texto do bloco é reusado byte-a-byte, sem
        recomputar o prefixo. As fontes adicionais, dependentes da pergunta,
        ficam de fora do bloco estável e da assinatura.
        """
        fundamentos_txt, resumos, assinatura = self._componentes(
            fundamentos, watchlist, ticker
        )
        repetido = cache is not None and cache[0] == assinatura
        if repetido:
            bloco = cache[1]
        else:
            bloco = self._renderizar_bloco(fundamentos_txt, resumos)
        documental = ContextoDocumental(
            resumos=resumos,
            preparar_texto=self.preparar_texto,
            confirmar=self.confirmar_leitura,
        )
        return ContextoChat(
            bloco_estavel=bloco,
            assinatura=assinatura,
            documentos=documental,
            fontes_adicionais=self.preparar_fontes_adicionais(pergunta),
            prefixo_repetido=repetido,
        )

    def montar_bloco(
        self: "MontarContextoChat",
        fundamentos: Mapping[str, object],
        watchlist: Iterable[str],
        ticker: str | None = None,
        cache: tuple[str, str] | None = None,
    ) -> tuple[str, str]:
        """Monta o bloco estável e a sua assinatura, reusando o cache se casar."""
        fundamentos_txt, resumos, assinatura = self._componentes(
            fundamentos, watchlist, ticker
        )
        if cache is not None and cache[0] == assinatura:
            return cache[1], assinatura
        return self._renderizar_bloco(fundamentos_txt, resumos), assinatura

    def _componentes(
        self: "MontarContextoChat",
        fundamentos: Mapping[str, object],
        watchlist: Iterable[str],
        ticker: str | None,
    ) -> tuple[str, str, str]:
        """Computa os componentes estáveis e a assinatura derivada do conteúdo."""
        resumos, _alvos = self._cascata.montar_resumos(ticker, watchlist)
        fundamentos_txt = montar_contexto_fundamentos(fundamentos, ticker, watchlist)
        assinatura = assinatura_bloco(
            self._conhecimento, fundamentos_txt, resumos
        )
        return fundamentos_txt, resumos, assinatura

    def _renderizar_bloco(
        self: "MontarContextoChat", fundamentos: str, resumos: str
    ) -> str:
        """Renderiza o bloco estável, em ordem determinística."""
        partes: list[str] = []
        if self._conhecimento:
            partes.extend(["## Conhecimento do FlowScope", self._conhecimento, ""])
        if fundamentos:
            partes.extend(["## Fundamentos carregados", fundamentos, ""])
        if resumos:
            partes.extend(["## Resumos de documentos", resumos, ""])
        return "\n".join(partes).rstrip("\n")

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
