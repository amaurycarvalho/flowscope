"""Protocolo JSON de navegação da árvore de conhecimento.

A LLM emite, a cada turno, um objeto ``{"resposta", "solicitacoes": [...]}``. O
parser é tolerante (bloco cercado, texto cru ou trecho entre chaves) e, sem JSON
reconhecido, todo o texto é tratado como resposta final. As operações válidas
são validadas, executadas na ordem da lista e agregadas em um único bloco
determinístico, sem timestamps.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field

from flowscope.application.chat.arvore import ArvoreConhecimento, ErroNavegacao
from flowscope.application.chat.seguranca_regex import (
    PadraoBloqueado,
    PadraoInvalido,
    compilar,
)

logger = logging.getLogger("flowscope")

#: Operações aceitas pelo protocolo.
OPERACOES = frozenset(
    {
        "listar",
        "obter",
        "contar",
        "existe",
        "buscar",
        "buscar_semantico",
        "resetar_navegacao",
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
    "resetar_navegacao": (),
}

#: Máximo de operações por turno.
MAX_OPERACOES = 8

#: Marcador do bloco de resultado de navegação.
MARCADOR_RESULTADO = "[RESULTADO_NAVEGACAO]"

_MARCADOR_JSON = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


@dataclass(frozen=True)
class Solicitacao:
    """Operação pedida pela LLM, com os seus campos."""

    op: str
    campos: dict = field(default_factory=dict)


@dataclass(frozen=True)
class RespostaProtocolo:
    """Resposta interpretada do turno."""

    resposta: str | None
    solicitacoes: list[Solicitacao] = field(default_factory=list)

    @property
    def final(self: RespostaProtocolo) -> bool:
        """Indica se a resposta é conclusiva (sem solicitações)."""
        return not self.solicitacoes


def extrair_json(texto: str) -> dict | None:
    """Extrai o objeto JSON da resposta, tentando formatos tolerantes."""
    if not texto:
        return None
    candidatos: list[str] = []
    cercado = _MARCADOR_JSON.search(texto)
    if cercado is not None:
        candidatos.append(cercado.group(1))
    candidatos.append(texto.strip())
    inicio, fim = texto.find("{"), texto.rfind("}")
    if 0 <= inicio < fim:
        candidatos.append(texto[inicio : fim + 1])
    for candidato in candidatos:
        try:
            dados = json.loads(candidato)
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(dados, dict) and "resposta" in dados:
            return dados
    return None


def _texto_ou_nulo(valor: object) -> str | None:
    """Normaliza o campo ``resposta`` para texto sem espaços ou ``None``."""
    if isinstance(valor, str):
        return valor.strip() or None
    return None


def _solicitacoes(itens: object) -> list[Solicitacao]:
    """Normaliza a lista de solicitações, descartando itens inválidos."""
    if not isinstance(itens, list):
        return []
    return [
        Solicitacao(op=item["op"], campos={k: v for k, v in item.items() if k != "op"})
        for item in itens
        if isinstance(item, dict) and isinstance(item.get("op"), str)
    ]


def interpretar(texto: str) -> RespostaProtocolo:
    """Interpreta a resposta da LLM, tolerando formatos e texto puro."""
    dados = extrair_json(texto)
    if dados is None:
        return RespostaProtocolo(resposta=_texto_ou_nulo((texto or "").strip()))
    return RespostaProtocolo(
        resposta=_texto_ou_nulo(dados.get("resposta")),
        solicitacoes=_solicitacoes(dados.get("solicitacoes")),
    )


def _erro_dict(motivo: str, detalhe: str, dica: str = "") -> dict:
    """Monta o erro estruturado devolvido à LLM, com dica quando houver."""
    erro = {"motivo": motivo, "detalhe": detalhe}
    if dica:
        erro["dica"] = dica
    return erro


def _registrar_erro(
    solicitacao: Solicitacao, caminho: object, motivo: str, detalhe: str
) -> None:
    """Registra em log um erro de navegação devolvido à LLM."""
    logger.warning(
        "Erro de navegação do chat: op=%s caminho=%s motivo=%s detalhe=%s",
        solicitacao.op,
        caminho,
        motivo,
        detalhe or "-",
    )


class ProtocoloNavegacao:
    """Valida, executa e serializa as operações de navegação."""

    def __init__(
        self: ProtocoloNavegacao,
        arvore: ArvoreConhecimento,
        max_operacoes: int = MAX_OPERACOES,
    ) -> None:
        """Guarda a árvore e o limite de operações por turno."""
        self._arvore = arvore
        self._max_operacoes = max_operacoes

    def validar(self: ProtocoloNavegacao, solicitacao: Solicitacao) -> None:
        """Valida a operação, levantando ``ErroNavegacao`` se inválida."""
        if solicitacao.op not in OPERACOES:
            raise ErroNavegacao(
                "op_desconhecida",
                solicitacao.op,
                "use uma das operações: " + ", ".join(sorted(OPERACOES)),
            )
        for campo in CAMPOS_OBRIGATORIOS[solicitacao.op]:
            if not solicitacao.campos.get(campo):
                raise ErroNavegacao(
                    "campo_ausente",
                    f"{solicitacao.op}:{campo}",
                    f"inclua o campo '{campo}' na operação {solicitacao.op}",
                )
        self._validar_campos(solicitacao)

    def _validar_campos(self: ProtocoloNavegacao, solicitacao: Solicitacao) -> None:
        """Valida o tipo dos campos e o uso de curinga, com dicas de correção."""
        caminho = solicitacao.campos.get("caminho")
        if caminho is not None and not isinstance(caminho, str):
            raise ErroNavegacao(
                "tipo_invalido", "caminho", "o campo 'caminho' deve ser texto"
            )
        if isinstance(caminho, str) and "*" in caminho:
            self._validar_curinga(solicitacao.op, caminho)
        for campo in ("regex", "consulta"):
            valor = solicitacao.campos.get(campo)
            if valor is not None and not isinstance(valor, str):
                raise ErroNavegacao(
                    "tipo_invalido", campo, f"o campo '{campo}' deve ser texto"
                )
        self._validar_em(solicitacao)
        self._validar_max(solicitacao)

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
    def _validar_em(solicitacao: Solicitacao) -> None:
        """Valida o campo opcional ``em`` (lista de nomes de campos)."""
        em = solicitacao.campos.get("em")
        if em is None:
            return
        if not isinstance(em, list) or not all(isinstance(x, str) for x in em):
            raise ErroNavegacao(
                "tipo_invalido",
                "em",
                "o campo 'em' deve ser uma lista de nomes de campos",
            )

    @staticmethod
    def _validar_max(solicitacao: Solicitacao) -> None:
        """Valida o campo opcional ``max`` (inteiro maior que zero)."""
        maximo = solicitacao.campos.get("max")
        if maximo is None:
            return
        if isinstance(maximo, bool) or not isinstance(maximo, int) or maximo <= 0:
            raise ErroNavegacao(
                "tipo_invalido",
                "max",
                "o campo 'max' deve ser um inteiro maior que zero",
            )

    def executar(
        self: ProtocoloNavegacao, solicitacoes: list[Solicitacao]
    ) -> list[dict]:
        """Executa as operações na ordem, agregando resultados estruturados."""
        if len(solicitacoes) > self._max_operacoes:
            excedente = solicitacoes[self._max_operacoes :]
            solicitacoes = solicitacoes[: self._max_operacoes]
            resultados = [self._executar_uma(s) for s in solicitacoes]
            resultados.append(
                {
                    "op": "limite_operacoes",
                    "erro": {"motivo": "limite_operacoes", "detalhe": f"{len(excedente)} excedentes"},
                }
            )
            return resultados
        return [self._executar_uma(s) for s in solicitacoes]

    def _executar_uma(self: ProtocoloNavegacao, solicitacao: Solicitacao) -> dict:
        """Executa uma operação, capturando o erro estruturado."""
        base = {"op": solicitacao.op}
        caminho = solicitacao.campos.get("caminho")
        if caminho:
            base["caminho"] = caminho
        try:
            self.validar(solicitacao)
            base["dados"] = self._despachar(solicitacao)
        except ErroNavegacao as exc:
            _registrar_erro(solicitacao, caminho, exc.motivo, exc.detalhe)
            base["erro"] = _erro_dict(exc.motivo, exc.detalhe, exc.dica)
        except PadraoBloqueado as exc:
            _registrar_erro(solicitacao, caminho, "regex_bloqueada", str(exc))
            base["erro"] = _erro_dict(
                "regex_bloqueada",
                str(exc),
                "simplifique o regex: evite quantificadores aninhados e backreferences",
            )
        except PadraoInvalido as exc:
            _registrar_erro(solicitacao, caminho, "regex_invalida", str(exc))
            base["erro"] = _erro_dict(
                "regex_invalida", str(exc), "corrija a sintaxe do regex"
            )
        except Exception as exc:
            logger.error(
                "Erro inesperado na navegação do chat: op=%s caminho=%s: %s",
                solicitacao.op,
                caminho,
                exc,
                exc_info=exc,
            )
            base["erro"] = _erro_dict(
                "erro_interno",
                type(exc).__name__,
                "a operação falhou; tente outra abordagem",
            )
        return base

    def _despachar(self: ProtocoloNavegacao, solicitacao: Solicitacao) -> object:
        """Resolve a operação na árvore."""
        campos = solicitacao.campos
        op = solicitacao.op
        if op == "listar":
            return [
                {"nome": no.nome, "caminho": no.caminho, "metadado": no.metadado}
                for no in self._arvore.listar(campos["caminho"])
            ]
        if op == "obter":
            return self._arvore.obter(campos["caminho"])
        if op == "contar":
            return self._arvore.contar(campos["caminho"])
        if op == "existe":
            return self._arvore.existe(campos["caminho"])
        if op == "buscar":
            padrao = compilar(campos["regex"])
            return self._arvore.buscar(
                campos["caminho"], padrao, em=campos.get("em"), limite=campos.get("max")
            )
        if op == "buscar_semantico":
            return self._arvore.buscar_semantico(
                campos["caminho"], campos["consulta"], limite=campos.get("max")
            )
        return "navegacao_descartada"

    @staticmethod
    def serializar(resultados: list[dict]) -> str:
        """Serializa os resultados em um bloco determinístico."""
        corpo = json.dumps({"resultados": resultados}, ensure_ascii=False)
        return f"{MARCADOR_RESULTADO} {corpo}"

    def executar_e_serializar(self: ProtocoloNavegacao, solicitacoes: list[Solicitacao]) -> str:
        """Executa as operações e devolve o bloco serializado."""
        return self.serializar(self.executar(solicitacoes))
