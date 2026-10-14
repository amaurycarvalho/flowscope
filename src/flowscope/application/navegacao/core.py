"""Núcleo único de navegação da árvore de conhecimento.

Concentra as operações canônicas (`listar`, `obter`, `contar`, `existe`,
`buscar`, `buscar_semantico` e o manifesto), a validação, os limites canônicos,
a paginação por cursor opaco, os erros estruturados recuperáveis e o
confinamento de leitura ao cache local. É reusado pelo chat (via adaptador
`ProtocoloNavegacao`), pelos subcomandos CLI `flowscope nav ...` e pelo servidor
MCP, garantindo paridade de comportamento entre as superfícies.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass

from flowscope.application.chat.arvore import (
    ArvoreConhecimento,
    ErroNavegacao,
    No,
    normalizar_caminho,
)
from flowscope.application.chat.manifesto import TETO_TOKENS, montar_manifesto
from flowscope.application.chat.seguranca_regex import (
    PadraoBloqueado,
    PadraoInvalido,
    compilar,
)
from flowscope.application.navegacao.cursor import codificar, decodificar

logger = logging.getLogger("flowscope")

#: Limite canônico de resultados de uma busca determinística.
LIMITE_BUSCA = 50

#: Tamanho do trecho devolvido em cada resultado de busca.
LIMITE_TRECHO = 200

#: Tamanho de página padrão da listagem.
TAMANHO_PAGINA_LISTAR = 100

#: Limite canônico de resultados da busca semântica.
LIMITE_SEMANTICO = 20

#: Limite padrão e teto de caracteres por página de conteúdo pesado de ``obter``.
LIMITE_PAGINA_PADRAO = 12000

#: Timeout de uma busca por regex, em milissegundos.
TIMEOUT_REGEX_MS = 100

#: Teto de tokens do manifesto.
TETO_TOKENS_MANIFESTO = TETO_TOKENS

#: Operações canônicas do núcleo (sem reset e sem execução em lote).
OPERACOES = frozenset(
    {
        "listar",
        "obter",
        "contar",
        "existe",
        "buscar",
        "buscar_semantico",
        "manifesto",
    }
)

#: Campos obrigatórios por operação.
CAMPOS_OBRIGATORIOS = {
    "listar": ("caminho",),
    "obter": ("caminho",),
    "contar": ("caminho",),
    "existe": ("caminho",),
    "buscar": ("caminho", "regex"),
    "buscar_semantico": ("caminho", "consulta"),
    "manifesto": (),
}

#: Operações de listagem que aceitam o campo opcional ``cursor``.
OPERACOES_COM_CURSOR = frozenset({"listar", "buscar", "buscar_semantico"})


@dataclass(frozen=True)
class Resultado:
    """Resultado de uma operação do núcleo.

    ``dados`` é o resultado estruturado; ``erro`` o erro estruturado de domínio
    (recuperável) e ``falha_interna`` marca a falha inesperada que as superfícies
    externas convertem em erro interno.
    """

    dados: object | None = None
    erro: dict | None = None
    falha_interna: bool = False


def _erro_dict(motivo: str, detalhe: str, dica: str = "") -> dict:
    """Monta o erro estruturado com motivo, detalhe e dica quando houver."""
    erro = {"motivo": motivo, "detalhe": detalhe}
    if dica:
        erro["dica"] = dica
    return erro


class NavegacaoCore:
    """Valida e executa as operações canônicas sobre a árvore de conhecimento."""

    def __init__(
        self: NavegacaoCore,
        arvore: ArvoreConhecimento,
        teto_tokens: int = TETO_TOKENS_MANIFESTO,
    ) -> None:
        """Guarda a árvore indexada e o teto de tokens do manifesto."""
        self._arvore = arvore
        self._teto_tokens = teto_tokens

    @property
    def arvore(self: NavegacaoCore) -> ArvoreConhecimento:
        """Árvore de conhecimento usada pelo núcleo."""
        return self._arvore

    # ── Validação ────────────────────────────────────────────────────

    def validar(self: NavegacaoCore, op: str, campos: dict) -> None:
        """Valida a operação e os seus campos, levantando ``ErroNavegacao``."""
        if op not in OPERACOES:
            raise ErroNavegacao(
                "op_desconhecida",
                op,
                "use uma das operações: " + ", ".join(sorted(OPERACOES)),
            )
        for campo in CAMPOS_OBRIGATORIOS[op]:
            if not campos.get(campo):
                raise ErroNavegacao(
                    "campo_ausente",
                    f"{op}:{campo}",
                    f"inclua o campo '{campo}' na operação {op}",
                )
        self._validar_campos(op, campos)

    def _validar_campos(self: NavegacaoCore, op: str, campos: dict) -> None:
        """Valida o tipo dos campos, o curinga e a paginação, com dicas."""
        caminho = campos.get("caminho")
        if caminho is not None and not isinstance(caminho, str):
            raise ErroNavegacao(
                "tipo_invalido", "caminho", "o campo 'caminho' deve ser texto"
            )
        if isinstance(caminho, str) and "*" in caminho:
            self._validar_curinga(op, caminho)
        for campo in ("regex", "consulta"):
            valor = campos.get(campo)
            if valor is not None and not isinstance(valor, str):
                raise ErroNavegacao(
                    "tipo_invalido", campo, f"o campo '{campo}' deve ser texto"
                )
        self._validar_em(campos)
        self._validar_max(campos)
        self._validar_paginacao(op, campos)
        self._validar_cursor(op, campos)

    @staticmethod
    def _validar_paginacao(op: str, campos: dict) -> None:
        """Valida os campos opcionais ``offset``/``limite`` de ``obter``."""
        if op != "obter":
            return
        offset = campos.get("offset")
        if offset is not None and (
            isinstance(offset, bool) or not isinstance(offset, int) or offset < 0
        ):
            raise ErroNavegacao(
                "tipo_invalido",
                "offset",
                "o campo 'offset' deve ser um inteiro maior ou igual a zero",
            )
        limite = campos.get("limite")
        if limite is not None and (
            isinstance(limite, bool) or not isinstance(limite, int) or limite <= 0
        ):
            raise ErroNavegacao(
                "tipo_invalido",
                "limite",
                "o campo 'limite' deve ser um inteiro maior que zero",
            )

    @staticmethod
    def _validar_cursor(op: str, campos: dict) -> None:
        """Valida o campo opcional ``cursor`` (texto nas operações de listagem)."""
        cursor = campos.get("cursor")
        if cursor is None:
            return
        if op not in OPERACOES_COM_CURSOR:
            raise ErroNavegacao(
                "tipo_invalido",
                "cursor",
                "o campo 'cursor' só é aceito em listar, buscar e buscar_semantico",
            )
        if not isinstance(cursor, str):
            raise ErroNavegacao(
                "tipo_invalido", "cursor", "o campo 'cursor' deve ser texto"
            )

    @staticmethod
    def _validar_curinga(op: str, caminho: str) -> None:
        """Valida o uso de curinga: só em ``contar`` e apenas como ``prefixo/*``."""
        if op != "contar":
            raise ErroNavegacao(
                "caminho_com_curinga",
                caminho,
                "o curinga '*' só é aceito em contar; use o caminho exato",
            )
        if caminho.count("*") != 1 or not caminho.endswith("/*"):
            raise ErroNavegacao(
                "curinga_invalido",
                caminho,
                "use um único '*' no final do caminho (ex.: /ramo/*)",
            )

    @staticmethod
    def _validar_em(campos: dict) -> None:
        """Valida o campo opcional ``em`` (lista de nomes de campos)."""
        em = campos.get("em")
        if em is None:
            return
        if not isinstance(em, list) or not all(isinstance(x, str) for x in em):
            raise ErroNavegacao(
                "tipo_invalido",
                "em",
                "o campo 'em' deve ser uma lista de nomes de campos",
            )

    @staticmethod
    def _validar_max(campos: dict) -> None:
        """Valida o campo opcional ``max`` (inteiro maior que zero)."""
        maximo = campos.get("max")
        if maximo is None:
            return
        if isinstance(maximo, bool) or not isinstance(maximo, int) or maximo <= 0:
            raise ErroNavegacao(
                "tipo_invalido",
                "max",
                "o campo 'max' deve ser um inteiro maior que zero",
            )

    # ── Execução ─────────────────────────────────────────────────────

    def executar(self: NavegacaoCore, op: str, campos: dict) -> Resultado:
        """Valida e executa uma operação, capturando o erro estruturado.

        Erros de domínio recuperáveis viram ``erro`` sem ``falha_interna``;
        falhas inesperadas viram ``erro_interno`` com ``falha_interna``. Em
        ambos os casos o núcleo permanece apto a executar novas operações.
        """
        try:
            self.validar(op, campos)
            return Resultado(dados=self._despachar(op, campos))
        except ErroNavegacao as exc:
            self._registrar(op, campos.get("caminho"), exc.motivo, exc.detalhe)
            return Resultado(erro=_erro_dict(exc.motivo, exc.detalhe, exc.dica))
        except PadraoBloqueado as exc:
            self._registrar(op, campos.get("caminho"), "regex_bloqueada", str(exc))
            return Resultado(
                erro=_erro_dict(
                    "regex_bloqueada",
                    str(exc),
                    "simplifique o regex: evite quantificadores aninhados e backreferences",
                )
            )
        except PadraoInvalido as exc:
            self._registrar(op, campos.get("caminho"), "regex_invalida", str(exc))
            return Resultado(
                erro=_erro_dict("regex_invalida", str(exc), "corrija a sintaxe do regex")
            )
        except Exception as exc:
            logger.error(
                "Erro inesperado na navegação: op=%s caminho=%s: %s",
                op,
                campos.get("caminho"),
                exc,
                exc_info=exc,
            )
            return Resultado(
                erro=_erro_dict(
                    "erro_interno",
                    type(exc).__name__,
                    "a operação falhou; tente outra abordagem",
                ),
                falha_interna=True,
            )

    @staticmethod
    def _registrar(op: str, caminho: object, motivo: str, detalhe: str) -> None:
        """Registra em log um erro estruturado devolvido à superfície."""
        logger.warning(
            "Erro de navegação: op=%s caminho=%s motivo=%s detalhe=%s",
            op,
            caminho,
            motivo,
            detalhe or "-",
        )

    def _despachar(self: NavegacaoCore, op: str, campos: dict) -> object:
        """Resolve a operação canônica na árvore."""
        if op == "listar":
            return self.listar(campos["caminho"], campos.get("cursor"))
        if op == "obter":
            return self.obter(
                campos["caminho"],
                offset=campos.get("offset"),
                limite=campos.get("limite"),
            )
        if op == "contar":
            return self.contar(campos["caminho"])
        if op == "existe":
            return self.existe(campos["caminho"])
        if op == "buscar":
            return self.buscar(
                campos["caminho"],
                campos["regex"],
                em=campos.get("em"),
                maximo=campos.get("max"),
                cursor=campos.get("cursor"),
            )
        if op == "buscar_semantico":
            return self.buscar_semantico(
                campos["caminho"],
                campos["consulta"],
                maximo=campos.get("max"),
                cursor=campos.get("cursor"),
            )
        return self.manifesto()

    # ── Operações ────────────────────────────────────────────────────

    def listar(self: NavegacaoCore, caminho: str, cursor: str | None = None) -> dict:
        """Lista os filhos imediatos em ordem determinística, com paginação."""
        normalizado = normalizar_caminho(caminho)
        inicio = decodificar(cursor, "listar", normalizado) if cursor else 0
        itens = sorted(self._arvore.listar(normalizado), key=lambda no: no.caminho)
        pagina = itens[inicio : inicio + TAMANHO_PAGINA_LISTAR]
        dados = {"itens": [_item(no) for no in pagina]}
        _anexar_cursor(dados, "listar", normalizado, inicio + len(pagina), len(itens))
        return dados

    def obter(
        self: NavegacaoCore,
        caminho: str,
        offset: int | None = None,
        limite: int | None = None,
    ) -> object:
        """Devolve o conteúdo do nó, paginando os nós de conteúdo pesado."""
        tamanho = None if limite is None else min(limite, LIMITE_PAGINA_PADRAO)
        return self._arvore.obter(caminho, offset=offset, limite=tamanho)

    def contar(self: NavegacaoCore, caminho: str) -> int:
        """Conta os nós da subárvore prefixada pelo caminho."""
        return self._arvore.contar(caminho)

    def existe(self: NavegacaoCore, caminho: str) -> bool:
        """Indica se o caminho existe na árvore."""
        return self._arvore.existe(caminho)

    def buscar(
        self: NavegacaoCore,
        caminho: str,
        regex: str,
        em: Iterable[str] | None = None,
        maximo: int | None = None,
        cursor: str | None = None,
    ) -> dict:
        """Busca determinística por regex, em ordem de caminho, com paginação."""
        normalizado = normalizar_caminho(caminho)
        inicio = decodificar(cursor, "buscar", normalizado) if cursor else 0
        padrao = compilar(regex, timeout_ms=TIMEOUT_REGEX_MS)
        limite = maximo or LIMITE_BUSCA
        dados, total = self._arvore.buscar_pagina(
            normalizado, padrao, em=em, deslocamento=inicio, limite=limite
        )
        _anexar_cursor(
            dados, "buscar", normalizado, inicio + len(dados["resultados"]), total
        )
        return dados

    def buscar_semantico(
        self: NavegacaoCore,
        caminho: str,
        consulta: str,
        maximo: int | None = None,
        cursor: str | None = None,
    ) -> dict:
        """Busca semântica opcional, com paginação por cursor quando há backend."""
        normalizado = normalizar_caminho(caminho)
        inicio = decodificar(cursor, "buscar_semantico", normalizado) if cursor else 0
        limite = maximo or LIMITE_SEMANTICO
        dados = self._arvore.buscar_semantico(
            normalizado, consulta, limite=inicio + limite
        )
        resultados = _ordenar_por_caminho(dados.get("resultados", []))
        pagina = resultados[inicio : inicio + limite]
        dados = {**dados, "resultados": pagina}
        _anexar_cursor(
            dados,
            "buscar_semantico",
            normalizado,
            inicio + len(pagina),
            len(resultados),
        )
        return dados

    def manifesto(self: NavegacaoCore) -> str:
        """Devolve o manifesto de navegação determinístico da árvore."""
        return montar_manifesto(self._arvore, teto_tokens=self._teto_tokens)


def _item(no: No) -> dict:
    """Serializa um nó de listagem com nome, caminho e metadado."""
    return {"nome": no.nome, "caminho": no.caminho, "metadado": no.metadado}


def _anexar_cursor(
    dados: dict, op: str, caminho: str, proximo: int, total: int
) -> None:
    """Acrescenta ``nextCursor`` apenas quando há mais resultados."""
    if proximo < total:
        dados["nextCursor"] = codificar(op, caminho, proximo)


def _ordenar_por_caminho(resultados: list) -> list:
    """Ordena itens com caminho de forma determinística, preservando os demais."""
    return sorted(
        resultados,
        key=lambda item: item.get("caminho", "")
        if isinstance(item, dict)
        else "",
    )
