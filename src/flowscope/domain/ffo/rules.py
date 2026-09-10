"""Tabela de regras versionada de classificação de componentes (RFC-010).

A classificação é determinística, independente do ticker e do gestor, e
conservadora: qualquer descrição que não corresponda a uma regra é ``UNKNOWN``
e não entra no FFO.
"""

from flowscope.domain.ffo.components import FFOComponentType

#: Versão da tabela de regras de classificação.
FFO_RULES_VERSION = "FFO_RULES_V1"

#: Regras avaliadas em ordem; o primeiro tipo que casar vence.
_RULES: tuple[tuple[FFOComponentType, tuple[str, ...]], ...] = (
    (
        FFOComponentType.NON_RECURRING,
        ("não recorrente", "nao recorrente", "extraordinár", "extraordinar"),
    ),
    (
        FFOComponentType.DISPOSAL,
        (
            "ganho na venda",
            "perda na venda",
            "resultado na venda",
            "ganho de capital",
            "alienação",
            "alienacao",
            "venda de ativo",
            "venda de cri",
        ),
    ),
    (
        FFOComponentType.FAIR_VALUE,
        (
            "valor justo",
            "marcação a mercado",
            "marcacao a mercado",
            "ajuste ao valor",
            "avaliação a mercado",
            "avaliacao a mercado",
            "mtm",
        ),
    ),
    (
        FFOComponentType.RECURRING,
        (
            "aluguel",
            "juros de cri",
            "rendimento de cri",
            "receita recorrente",
            "receita de venda de imóveis",
            "receita de venda de imoveis",
            "receita de serviços",
            "receita de servicos",
            "estacionamento",
            "manutenção",
            "manutencao",
            "conservação",
            "conservacao",
            "administração",
            "administracao",
            "administrativ",
            "gestão",
            "gestao",
            "custódia",
            "custodia",
            "auditoria",
            "consultoria",
            "comissões",
            "comissoes",
            "taxa de administração",
            "taxa de performance",
        ),
    ),
)


def classificar_componente(descricao: str) -> FFOComponentType:
    """Classifica a descrição de um componente em um tipo do FFO."""
    texto = (descricao or "").strip().lower()
    if not texto:
        return FFOComponentType.UNKNOWN
    for tipo, termos in _RULES:
        if any(termo in texto for termo in termos):
            return tipo
    return FFOComponentType.UNKNOWN
