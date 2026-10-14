"""Cursor opaco da paginação das listagens de navegação.

O cursor é ``base64url`` de um JSON determinístico ``{"v", "op", "caminho",
"pos"}``. É autocontido (não depende de estado de sessão), versionado e
vinculado à operação e ao caminho que o originaram, de modo que reuso indevido
entre tools ou caminhos seja recusado.
"""

from __future__ import annotations

import base64
import json

from flowscope.application.chat.arvore import ErroNavegacao

#: Versão atual do formato do cursor.
VERSAO_CURSOR = 1

#: Dica padrão de recuperação para cursors inválidos.
_DICA = "refaça a operação sem cursor para obter uma nova página"


def codificar(op: str, caminho: str, pos: int) -> str:
    """Codifica um cursor opaco para a operação, o caminho e a posição."""
    payload = {"v": VERSAO_CURSOR, "op": op, "caminho": caminho, "pos": pos}
    bruto = json.dumps(
        payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return base64.urlsafe_b64encode(bruto).rstrip(b"=").decode("ascii")


def decodificar(token: str, op: str, caminho: str) -> int:
    """Decodifica e valida o cursor, devolvendo a posição.

    Recusa cursors malformados, de versão desconhecida ou originados de outra
    operação/caminho com ``ErroNavegacao`` de motivo ``cursor_invalido``.
    """
    dados = _desserializar(token)
    if dados.get("v") != VERSAO_CURSOR:
        raise _invalido("versao_desconhecida", token)
    if dados.get("op") != op or dados.get("caminho") != caminho:
        raise _invalido("operacao_ou_caminho_divergente", token)
    pos = dados.get("pos")
    if isinstance(pos, bool) or not isinstance(pos, int) or pos < 0:
        raise _invalido("posicao_invalida", token)
    return pos


def _desserializar(token: object) -> dict:
    """Decodifica o base64url e o JSON do cursor, recusando entradas inválidas."""
    if not isinstance(token, str) or not token:
        raise _invalido("malformado", token)
    try:
        recheio = "=" * (-len(token) % 4)
        bruto = base64.urlsafe_b64decode(token + recheio)
        dados = json.loads(bruto.decode("utf-8"))
    except ValueError as exc:
        raise _invalido("malformado", token) from exc
    if not isinstance(dados, dict):
        raise _invalido("malformado", token)
    return dados


def _invalido(motivo: str, token: object) -> ErroNavegacao:
    """Monta o erro estruturado de cursor inválido."""
    return ErroNavegacao("cursor_invalido", f"{motivo}: {token!r}", _DICA)
