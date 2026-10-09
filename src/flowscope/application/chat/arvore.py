"""Árvore de conhecimento navegável do estado local do FlowScope.

A árvore é montada estritamente a partir do estado já em cache e expõe cada
informação como um nó resolvível por caminho canônico. Nós internos devolvem os
filhos imediatos (nome e metadado curto); nós folha devolvem conteúdo. A árvore
não resume, não extrai, não baixa e não consulta a B3/CVM.

As operações de leitura são determinísticas e sem efeitos colaterais, de modo a
poderem ser validadas e executadas pelo protocolo de navegação da LLM.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import PurePosixPath

from flowscope.application.chat.seguranca_regex import TimeoutRegex

#: Motivo devolvido quando não há backend de busca semântica disponível.
MOTIVO_SEM_INDICE = "indice_indisponivel"

#: Limite padrão de resultados de uma busca.
MAX_RESULTADOS = 50

#: Tamanho do trecho devolvido em cada resultado de busca.
TAMANHO_TRECHO = 200

#: Limite padrão de caracteres por página de conteúdo pesado.
LIMITE_PAGINA_PADRAO = 12000


@dataclass
class No:
    """Nó da árvore de conhecimento, folha ou interno.

    ``campos`` mapeia o nome do campo para o texto pesquisável do nó;
    ``carregar`` permite adiar a leitura do conteúdo pesado até ``obter``;
    ``campo_pesado`` nomeia o campo cujo valor só existe sob demanda (não
    pesquisável por regex, mas acessível por ``obter``).
    """

    caminho: str
    nome: str
    metadado: str = ""
    conteudo: str = ""
    filhos: list[No] = field(default_factory=list)
    campos: dict[str, str] = field(default_factory=dict)
    semantico: str = ""
    carregar: Callable[[], str] | None = None
    campo_pesado: str = ""

    @property
    def folha(self: No) -> bool:
        """Indica se o nó não tem filhos."""
        return not self.filhos

    def filho(self: No, no: No) -> No:
        """Acrescenta um filho e devolve o filho acrescentado."""
        self.filhos.append(no)
        return no


class ErroNavegacao(Exception):
    """Erro de navegação devolvido à LLM de forma estruturada.

    ``dica`` sugere à LLM como se recuperar (ex.: trocar ``listar`` por
    ``obter`` numa folha), tornando o erro acionável em vez de parecer
    uma indisponibilidade.
    """

    def __init__(
        self: ErroNavegacao, motivo: str, detalhe: str = "", dica: str = ""
    ) -> None:
        """Guarda o motivo canônico, um detalhe legível e uma dica de recuperação."""
        self.motivo = motivo
        self.detalhe = detalhe
        self.dica = dica
        super().__init__(motivo, detalhe, dica)


def normalizar_caminho(caminho: str) -> str:
    """Normaliza um caminho canônico: absoluto, sem barra final nem duplicada."""
    texto = (caminho or "").strip().replace("//", "/")
    if not texto.startswith("/"):
        texto = "/" + texto
    if len(texto) > 1 and texto.endswith("/"):
        texto = texto.rstrip("/")
    return texto


def no_interno(caminho: str, nome: str, metadado: str = "") -> No:
    """Cria um nó interno (com filhos previstos)."""
    return No(caminho=normalizar_caminho(caminho), nome=nome, metadado=metadado)


def no_folha(
    caminho: str,
    nome: str,
    conteudo: str = "",
    metadado: str = "",
    campos: Mapping[str, str] | None = None,
    carregar: Callable[[], str] | None = None,
    campo_pesado: str = "",
) -> No:
    """Cria um nó folha com conteúdo (direto ou carregado sob demanda)."""
    return No(
        caminho=normalizar_caminho(caminho),
        nome=nome,
        metadado=metadado,
        conteudo=conteudo,
        campos=dict(campos or {}),
        carregar=carregar,
        campo_pesado=campo_pesado,
    )


@dataclass(frozen=True)
class ItemResultado:
    """Item devolvido por ``buscar``/``buscar_semantico``."""

    caminho: str
    campo: str
    trecho: str


class ArvoreConhecimento:
    """Índice de caminhos em memória sobre uma raiz de nós."""

    def __init__(
        self: ArvoreConhecimento,
        raiz: No,
        assinatura: str = "",
        backend_semantico: object | None = None,
        max_resultados: int = MAX_RESULTADOS,
    ) -> None:
        """Indexa a árvore e guarda a assinatura e o backend semântico."""
        self._raiz = raiz
        self._assinatura = assinatura
        self._backend = backend_semantico
        self._max_resultados = max_resultados
        self._indice: dict[str, No] = {}
        self._indexar(raiz)

    @property
    def assinatura(self: ArvoreConhecimento) -> str:
        """Assinatura do estado que originou a árvore."""
        return self._assinatura

    @property
    def raiz(self: ArvoreConhecimento) -> No:
        """Nó raiz da árvore."""
        return self._raiz

    def _indexar(self: ArvoreConhecimento, no: No) -> None:
        """Recursivamente registra cada nó pelo seu caminho."""
        self._indice[no.caminho] = no
        for filho in no.filhos:
            self._indexar(filho)

    def existe(self: ArvoreConhecimento, caminho: str) -> bool:
        """Indica se o caminho existe na árvore."""
        return normalizar_caminho(caminho) in self._indice

    def listar(self: ArvoreConhecimento, caminho: str) -> list[No]:
        """Devolve os filhos imediatos de um nó interno."""
        no = self._exigir(caminho)
        if no.folha:
            raise ErroNavegacao(
                "nao_interno",
                normalizar_caminho(caminho),
                "nó folha não tem filhos; use obter(caminho) para ler o conteúdo",
            )
        return list(no.filhos)

    def obter(
        self: ArvoreConhecimento,
        caminho: str,
        offset: int | None = None,
        limite: int | None = None,
    ) -> str | dict:
        """Devolve o conteúdo de um nó folha, carregando-o sob demanda.

        Nós de conteúdo pesado (``campo_pesado``) devolvem uma página: o trecho
        ``[offset, offset+limite)`` com o total, o ``offset`` e o ``limite``
        aplicados e o indicador ``continua``. Sem ``offset``/``limite``,
        devolvem a página padrão a partir do início. Os demais nós devolvem o
        conteúdo integral como texto.
        """
        no = self._exigir(caminho)
        if not no.folha:
            raise ErroNavegacao(
                "nao_folha",
                normalizar_caminho(caminho),
                "nó interno não tem conteúdo; use listar(caminho) para ver os filhos",
            )
        conteudo = self._carregar_conteudo(no)
        if no.campo_pesado:
            return self._paginar(conteudo, offset, limite)
        return conteudo

    @staticmethod
    def _carregar_conteudo(no: No) -> str:
        """Materializa o conteúdo de um nó, adiando a leitura até o primeiro uso."""
        if not no.conteudo and no.carregar is not None:
            no.conteudo = no.carregar() or ""
        return no.conteudo

    @staticmethod
    def _paginar(conteudo: str, offset: int | None, limite: int | None) -> dict:
        """Recorta uma página do conteúdo pesado e sinaliza a continuação."""
        inicio = offset or 0
        tamanho = limite or LIMITE_PAGINA_PADRAO
        total = len(conteudo)
        trecho = conteudo[inicio : inicio + tamanho]
        return {
            "texto": trecho,
            "total": total,
            "offset": inicio,
            "limite": tamanho,
            "continua": inicio + len(trecho) < total,
        }

    def contar(self: ArvoreConhecimento, caminho: str) -> int:
        """Conta os nós da subárvore prefixada pelo caminho.

        Um ``*`` no caminho é tratado como coringa: conta apenas os nós sob o
        prefixo anterior ao coringa (os filhos), sem incluir o prefixo.
        """
        normalizado = normalizar_caminho(caminho)
        if "*" in normalizado:
            prefixo = normalizado.split("*", 1)[0].rstrip("/")
            return sum(
                1 for caminho_no in self._indice if caminho_no.startswith(prefixo + "/")
            )
        no = self._exigir(normalizado)
        return sum(
            1
            for caminho_no in self._indice
            if caminho_no == no.caminho or caminho_no.startswith(no.caminho + "/")
        )

    def buscar(
        self: ArvoreConhecimento,
        caminho: str,
        padrao: object,
        em: Iterable[str] | None = None,
        limite: int | None = None,
    ) -> dict:
        """Busca nós cujos campos casam com o padrão compilado."""
        base = self._exigir(caminho)
        limite_max = limite or self._max_resultados
        campos = set(em) if em else None
        self._checar_campos(base, campos)
        resultados: list[ItemResultado] = []
        truncado = False
        for no in self._subarvore(base):
            alvo = self._campos_alvo(no, campos)
            for campo, texto in alvo.items():
                if self._casa(padrao, texto):
                    resultados.append(ItemResultado(no.caminho, campo, texto[:TAMANHO_TRECHO]))
                    break
            if len(resultados) >= limite_max:
                truncado = True
                break
        return self._montar_busca(
            resultados, truncado, self._pedido_pesado(base, campos)
        )

    def _checar_campos(
        self: ArvoreConhecimento, base: No, campos: set[str] | None
    ) -> None:
        """Recusa ``em`` que nomeia campos inexistentes no ramo, com dica."""
        if not campos:
            return
        disponiveis: set[str] = set()
        for no in self._subarvore(base):
            expos = set(no.campos)
            if no.campo_pesado:
                expos.add(no.campo_pesado)
            if campos & expos:
                return
            disponiveis.update(expos)
        dica = "campos disponíveis: " + (
            ", ".join(sorted(disponiveis)) if disponiveis else "nenhum"
        )
        raise ErroNavegacao("campo_inexistente", ", ".join(sorted(campos)), dica)

    def _pedido_pesado(
        self: ArvoreConhecimento, base: No, campos: set[str] | None
    ) -> set[str]:
        """Devolve os campos pesados pedidos que não são pesquisáveis."""
        if not campos:
            return set()
        pesados = {
            no.campo_pesado
            for no in self._subarvore(base)
            if no.campo_pesado in campos
        }
        return pesados

    @staticmethod
    def _montar_busca(
        resultados: list[ItemResultado], truncado: bool, pesados: set[str]
    ) -> dict:
        """Monta o resultado da busca, com dica quando não houve casamento."""
        saida = {
            "resultados": [
                {"caminho": r.caminho, "campo": r.campo, "trecho": r.trecho}
                for r in resultados
            ],
            "truncado": truncado,
        }
        if not resultados:
            if pesados:
                saida["dica"] = (
                    "campos "
                    + ", ".join(sorted(pesados))
                    + " são carregados sob demanda e não pesquisáveis; use obter(caminho)"
                )
            else:
                saida["dica"] = (
                    "nenhum nó casou; verifique a grafia, use termos mais amplos "
                    "ou listar(caminho)"
                )
        return saida

    def buscar_semantico(
        self: ArvoreConhecimento,
        caminho: str,
        consulta: str,
        limite: int | None = None,
    ) -> dict:
        """Delega a busca semântica ao backend, se houver.

        Sem backend, devolve vazio com o motivo ``indice_indisponivel`` sem
        alterar o manifesto nem o protocolo.
        """
        base = self._exigir(caminho)
        if self._backend is None:
            return {
                "resultados": [],
                "motivo": MOTIVO_SEM_INDICE,
                "dica": "sem índice vetorial; use buscar(caminho, regex) ou listar",
            }
        return self._backend.buscar(  # type: ignore[attr-defined]
            base.caminho, consulta, limite or self._max_resultados
        )

    def _exigir(self: ArvoreConhecimento, caminho: str) -> No:
        """Devolve o nó do caminho ou levanta ``ErroNavegacao``.

        A dica aponta o **ancestral existente mais próximo**, que pode não ser o
        pai imediato (ex.: uma chave de notícia errada), para que a LLM liste um
        caminho realmente válido.
        """
        normalizado = normalizar_caminho(caminho)
        no = self._indice.get(normalizado)
        if no is not None:
            return no
        ancestral = self._ancestral_existente(normalizado)
        raise ErroNavegacao(
            "caminho_invalido",
            normalizado,
            f"caminho não existe; use existe(caminho) ou listar({ancestral})",
        )

    def _ancestral_existente(self: ArvoreConhecimento, caminho: str) -> str:
        """Devolve o ancestral existente mais próximo do caminho, ou ``/``."""
        partes = caminho.strip("/").split("/")
        for corte in range(len(partes) - 1, 0, -1):
            candidato = "/" + "/".join(partes[:corte])
            if candidato in self._indice:
                return candidato
        return "/" if "/" in self._indice else caminho

    def _subarvore(self: ArvoreConhecimento, base: No) -> list[No]:
        """Lista a base e todos os seus descendentes, em ordem de caminho."""
        prefixo = base.caminho if base.caminho != "/" else ""
        return [
            no
            for caminho, no in self._indice.items()
            if caminho == base.caminho or caminho.startswith(prefixo + "/")
        ]

    @staticmethod
    def _campos_alvo(no: No, campos: set[str] | None) -> dict[str, str]:
        """Seleciona os campos pesquisáveis do nó."""
        if not campos:
            return dict(no.campos)
        return {campo: no.campos[campo] for campo in campos if campo in no.campos}

    @staticmethod
    def _casa(padrao: object, texto: str) -> bool:
        """Avalia o padrão compilado sobre o texto, traduzindo o timeout."""
        try:
            if hasattr(padrao, "buscar"):
                return bool(padrao.buscar(texto))  # type: ignore[attr-defined]
            return bool(padrao.search(texto))  # type: ignore[attr-defined]
        except TimeoutRegex as exc:
            raise ErroNavegacao(
                "timeout_regex",
                str(exc),
                "regex lenta; use um padrão mais simples ou listar()",
            ) from exc


def ramo_flowscope(
    meta: Mapping[str, str],
    abas: Mapping[str, str] | None = None,
    subabas: Mapping[str, Mapping[str, str]] | None = None,
    indicadores: Mapping[str, str] | None = None,
) -> No:
    """Monta os ramos ``/flowscope/*`` a partir do conhecimento da ferramenta.

    Ramos internos sem itens são omitidos: como não têm filhos, seriam folhas
    vazias e induziriam a LLM a ``listar`` um nó não-listável.
    """
    raiz = no_interno("/flowscope", "flowscope")
    for chave in ("apresentacao", "licenca", "versao", "release_date", "repositorio"):
        if chave in meta:
            raiz.filho(
                no_folha(
                    f"/flowscope/meta/{chave}",
                    chave,
                    conteudo=meta[chave],
                    campos={"meta": meta[chave]},
                )
            )
    if abas:
        abas_no = no_interno("/flowscope/abas", "abas")
        for nome, proposito in abas.items():
            aba = no_folha(
                f"/flowscope/abas/{nome}",
                nome,
                conteudo=proposito,
                metadado=proposito,
                campos={"proposito": proposito},
            )
            for sub_nome, sub_proposito in (subabas or {}).get(nome, {}).items():
                aba.filhos.append(
                    no_folha(
                        f"/flowscope/abas/{nome}/subabas/{sub_nome}",
                        sub_nome,
                        conteudo=sub_proposito,
                        metadado=sub_proposito,
                        campos={"proposito": sub_proposito},
                    )
                )
            abas_no.filho(aba)
        raiz.filho(abas_no)
    if indicadores:
        indicadores_no = no_interno("/flowscope/indicadores", "indicadores")
        for nome, proposito in indicadores.items():
            indicadores_no.filho(
                no_folha(
                    f"/flowscope/indicadores/{nome}",
                    nome,
                    conteudo=proposito,
                    metadado=proposito,
                    campos={"proposito": proposito},
                )
            )
        raiz.filho(indicadores_no)
    return raiz


def ramo_fundamentos(
    tickers: Iterable[str] = (),
    campos: Mapping[str, str] | None = None,
    valores: Mapping[str, str] | None = None,
) -> No:
    """Monta os ramos ``/fundamentos/*`` a partir da tabela carregada.

    Sub-ramos sem itens são omitidos para não expor nós vazios como folhas.
    """
    raiz = no_interno("/fundamentos", "fundamentos")
    if tickers:
        tickers_no = no_interno("/fundamentos/tickers", "tickers")
        for ticker in tickers:
            tickers_no.filho(
                no_folha(
                    f"/fundamentos/tickers/{ticker}",
                    ticker,
                    conteudo=ticker,
                    campos={"ticker": ticker},
                )
            )
        raiz.filho(tickers_no)
    if campos:
        campos_no = no_interno("/fundamentos/campos", "campos")
        for nome, proposito in campos.items():
            campos_no.filho(
                no_folha(
                    f"/fundamentos/campos/{nome}",
                    nome,
                    conteudo=proposito,
                    metadado=proposito,
                    campos={"proposito": proposito},
                )
            )
        raiz.filho(campos_no)
    if valores:
        valores_no = no_interno("/fundamentos/valores", "valores")
        for ticker, linha in valores.items():
            valores_no.filho(
                no_folha(
                    f"/fundamentos/valores/{ticker}",
                    ticker,
                    conteudo=linha,
                    campos={"ticker": ticker, "valor": linha},
                )
            )
        raiz.filho(valores_no)
    return raiz


def nome_de(caminho: str) -> str:
    """Deriva o nome de exibição de um caminho."""
    return PurePosixPath(normalizar_caminho(caminho)).name
