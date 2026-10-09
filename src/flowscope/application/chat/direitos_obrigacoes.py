"""Ramo ``/direitos-obrigacoes`` da árvore de conhecimento.

Reserva o lugar para os direitos (ativos) e as obrigações (passivos) de um
ticker, preenchidos por changes futuras. Hoje os dois nós são folhas-placeholder
com a mensagem explícita de ausência de dados: no modelo de árvore, um nó sem
filhos é folha; quando uma change futura anexar filhos, o nó deixa de ser folha
automaticamente, preservando o caminho canônico.
"""

from __future__ import annotations

from flowscope.application.chat.arvore import No, no_folha, no_interno
from flowscope.application.documentos.mensagens import mensagem_placeholder

#: Segmentos e nomes dos sub-ramos placeholder.
_SUB_RAMOS = (("direitos", "direitos"), ("obrigacoes", "obrigacoes"))


class FonteDireitosObrigacoes:
    """Provedor do ramo ``/direitos-obrigacoes`` como placeholder navegável."""

    def construir(self: FonteDireitosObrigacoes) -> No:
        """Constrói o ramo com os sub-ramos Direitos e Obrigações vazios."""
        raiz = no_interno("/direitos-obrigacoes", "direitos e obrigacoes")
        for segmento, nome in _SUB_RAMOS:
            conteudo = mensagem_placeholder(segmento)
            raiz.filho(
                no_folha(
                    f"/direitos-obrigacoes/{segmento}",
                    nome,
                    conteudo=conteudo,
                    campos={"situacao": conteudo},
                )
            )
        return raiz
