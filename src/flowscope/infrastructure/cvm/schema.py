"""Descoberta e versionamento de schema do Informe Mensal da CVM (RFC-009)."""

#: Mapeamento canônico → aliases aceitos (nomes atuais e legados).
COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "cnpj": ("CNPJ_Fundo_Classe", "CNPJ_Fundo"),
    "nome": ("Nome_Fundo_Classe", "Nome_Fundo"),
    "tipo": ("Tipo_Fundo_Classe", "Tipo_Fundo"),
    "competencia": ("Data_Referencia", "DT_COMPTC"),
    "patrimonio": ("VL_PATRIM_LIQ",),
    "cotas": ("QT_COTA", "QUANT_COTA"),
    "cotistas": ("NR_COTST",),
    "versao": ("Versao", "VERSAO", "Nu_Versao"),
    "recebimento": ("Data_Recebimento", "DT_RECEB", "Data_Entrega"),
}

#: Colunas canônicas obrigatórias para processar um CSV.
REQUIRED_COLUMNS = ("cnpj", "competencia", "patrimonio", "cotas")


class CvmSchemaError(ValueError):
    """Erro quando o esquema do dataset da CVM não corresponde ao esperado."""


def _indice_ci(colunas: object) -> dict[str, str]:
    """Indexa os nomes físicos das colunas por sua forma minúscula."""
    return {str(coluna).strip().lower(): str(coluna) for coluna in colunas}


def _coluna_fisica(indice: dict[str, str], canonico: str) -> str | None:
    """Retorna o nome físico da coluna canônica, ou ``None``."""
    for candidato in COLUMN_ALIASES[canonico]:
        fisica = indice.get(candidato.lower())
        if fisica is not None:
            return fisica
    return None


def resolver_coluna(colunas: object, canonico: str) -> str:
    """Retorna o nome físico da coluna para o campo canônico informado."""
    fisica = _coluna_fisica(_indice_ci(colunas), canonico)
    if fisica is None:
        raise CvmSchemaError(f"Coluna obrigatória ausente: {canonico}")
    return fisica


def validar_schema(colunas: object) -> None:
    """Valida a presença das colunas obrigatórias do Informe Mensal."""
    indice = _indice_ci(colunas)
    for canonico in REQUIRED_COLUMNS:
        if _coluna_fisica(indice, canonico) is None:
            raise CvmSchemaError(f"Coluna obrigatória ausente: {canonico}")


def tem_coluna_identidade(colunas: object) -> bool:
    """Indica se o conjunto de colunas pertence ao Informe Mensal."""
    return _coluna_fisica(_indice_ci(colunas), "cnpj") is not None


def mapear_linha(linha: dict, colunas: object) -> dict:
    """Mapeia uma linha bruta para as chaves canônicas do schema."""
    indice = _indice_ci(colunas)
    return {
        canonico: linha.get(_coluna_fisica(indice, canonico))
        for canonico in COLUMN_ALIASES
    }


def mapear_com_aliases(linha: dict, colunas: object, aliases: dict) -> dict:
    """Mapeia uma linha para chaves canônicas usando um conjunto de aliases."""
    indice = _indice_ci(colunas)
    resultado: dict = {}
    for canonico, candidatos in aliases.items():
        fisica = None
        for candidato in candidatos:
            fisica = indice.get(candidato.lower())
            if fisica is not None:
                break
        resultado[canonico] = linha.get(fisica) if fisica else None
    return resultado


def validar_aliases(colunas: object, aliases: dict, obrigatorias: object) -> None:
    """Valida a presença das colunas obrigatórias para um conjunto de aliases."""
    indice = _indice_ci(colunas)
    for canonico in obrigatorias:
        if not any(
            candidato.lower() in indice
            for candidato in aliases.get(canonico, ())
        ):
            raise CvmSchemaError(f"Coluna obrigatória ausente: {canonico}")


def tem_alias(colunas: object, aliases: dict, canonico: str) -> bool:
    """Indica se alguma coluna do conjunto corresponde ao campo canônico."""
    indice = _indice_ci(colunas)
    return any(
        candidato.lower() in indice
        for candidato in aliases.get(canonico, ())
    )
