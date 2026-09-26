"""Whitelist e classificação por tipo das notícias do Plantão B3.

O título é normalizado (sem caixa, acentos e espaços duplicados) e comparado
com fronteira de palavra. A whitelist define quais eventos de mercado são
excepcionais; os tipos típicos agrupam cada evento na árvore da "Geral", com
``Outros`` como fallback.
"""

import re
import unicodedata

#: Eventos de mercado considerados excepcionais (fora da curva). Somente
#: notícias cujo título corresponda a um destes termos são carregadas.
TERMOS_EXCEPCIONAIS = (
    "Suspensão de negociação",
    "Suspensão negociação",
    "Revogação suspensão",
    "Reabertura de negociação",
    "Retirada de negociação",
    "Negociação não contínua",
    "Saída da negociação não contínua",
    "Alteração do nome de pregão",
    "Início de negociação",
    "Prorrogação do início de negociação",
    "Adiamento do início",
    "Adiamento da abertura",
    "Suspensão do registro",
    "Cancelamento do registro",
    "Cancelamento de registro",
    "Cancelamento de listagem",
    "Incorporação",
    "Fusão",
    "Cisão",
    "Reorganização",
    "Recuperação judicial",
    "Recuperação extrajudicial",
    "Pedido de recuperação",
    "Proc. recuperação",
    "Proc recuperação",
    "Falência",
    "Liquidação",
    "Liquidação extrajudicial",
    "Intervenção",
    "Grupamento",
    "Desdobramento",
    "Bonificação",
    "Redução de capital",
    "Aumento de capital",
    "Amortização",
    "Deslistagem",
    "Conversão de categoria",
    "Deixam de ser negociadas",
    "Oferta pública",
    "Oferta de ações",
    "OPA",
    "Modificação da oferta",
    "Modificação de oferta",
    "Mod. de oferta",
    "Aquisição de participação",
    "Alienação de participação",
    "Direito de preferência",
    "Mudança de auditor",
    "Ato homologatório",
    "Transação entre partes relacionadas",
    "Esclarecimentos",
    "Solicitou esclarecimentos",
    "Oscilação atípica",
)


def normalizar_texto(texto: str) -> str:
    """Normaliza texto para comparação: sem caixa, acentos e espaços duplicados."""
    decomposto = unicodedata.normalize("NFKD", texto or "")
    sem_acento = "".join(
        caractere
        for caractere in decomposto
        if not unicodedata.combining(caractere)
    )
    return re.sub(r"\s+", " ", sem_acento.lower()).strip()


def _padroes(termos: tuple[str, ...]) -> tuple[re.Pattern[str], ...]:
    """Compila os termos normalizados com fronteira de palavra."""
    return tuple(
        re.compile(r"\b" + re.escape(normalizar_texto(termo)) + r"\b")
        for termo in termos
    )


#: Regex dos termos excepcionais normalizados, com fronteira de palavra.
_PADROES_EXCEPCIONAIS = _padroes(TERMOS_EXCEPCIONAIS)

#: Tipos típicos de notícia e os termos da whitelist que os caracterizam.
#: A ordem define a prioridade de classificação quando mais de um tipo casa.
TIPOS_NOTICIA = (
    (
        "Negociação",
        (
            "Suspensão de negociação",
            "Suspensão negociação",
            "Revogação suspensão",
            "Reabertura de negociação",
            "Retirada de negociação",
            "Negociação não contínua",
            "Saída da negociação não contínua",
            "Alteração do nome de pregão",
            "Início de negociação",
            "Prorrogação do início de negociação",
            "Adiamento do início",
            "Adiamento da abertura",
            "Deixam de ser negociadas",
        ),
    ),
    (
        "Listagem e Registro",
        (
            "Suspensão do registro",
            "Cancelamento do registro",
            "Cancelamento de registro",
            "Cancelamento de listagem",
            "Deslistagem",
            "Conversão de categoria",
        ),
    ),
    (
        "Ofertas e OPA",
        (
            "Oferta pública",
            "Oferta de ações",
            "OPA",
            "Modificação da oferta",
            "Modificação de oferta",
            "Mod. de oferta",
            "Direito de preferência",
        ),
    ),
    ("Participações", ("Aquisição de participação", "Alienação de participação")),
    (
        "Reorganização Societária",
        ("Incorporação", "Fusão", "Cisão", "Reorganização"),
    ),
    (
        "Recuperação e Liquidação",
        (
            "Recuperação judicial",
            "Recuperação extrajudicial",
            "Pedido de recuperação",
            "Proc. recuperação",
            "Proc recuperação",
            "Falência",
            "Liquidação",
            "Liquidação extrajudicial",
            "Intervenção",
        ),
    ),
    (
        "Eventos de Capital",
        (
            "Grupamento",
            "Desdobramento",
            "Bonificação",
            "Redução de capital",
            "Aumento de capital",
            "Amortização",
        ),
    ),
    (
        "Governança e Auditoria",
        (
            "Mudança de auditor",
            "Ato homologatório",
            "Transação entre partes relacionadas",
        ),
    ),
    (
        "Esclarecimentos e Oscilações",
        ("Esclarecimentos", "Solicitou esclarecimentos", "Oscilação atípica"),
    ),
)

#: Tipo atribuído às notícias que não se enquadram em um tipo típico.
TIPO_OUTROS = "Outros"

#: Padrões compilados por tipo, na ordem de classificação.
_PADROES_TIPOS = tuple((tipo, _padroes(termos)) for tipo, termos in TIPOS_NOTICIA)


def noticia_excepcional(titulo: str) -> bool:
    """Indica se o título corresponde a um evento de mercado excepcional."""
    normalizado = normalizar_texto(titulo)
    return any(padrao.search(normalizado) for padrao in _PADROES_EXCEPCIONAIS)


def classificar_tipo(titulo: str) -> str:
    """Classifica o título em um tipo típico de notícia, ou ``TIPO_OUTROS``."""
    normalizado = normalizar_texto(titulo)
    for tipo, padroes in _PADROES_TIPOS:
        if any(padrao.search(normalizado) for padrao in padroes):
            return tipo
    return TIPO_OUTROS
