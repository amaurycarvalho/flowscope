"""Parsers e join dos Informes Mensais de CRI/CRA (SECURIT) da CVM."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, replace
from datetime import date

from flowscope.domain.renda_fixa import (
    PapelTitulo,
    TipoTitulo,
    TituloRendaFixa,
    id_curto,
)
from flowscope.infrastructure.cvm.renda_fixa_common import (
    codigo_cetip,
    data,
    decimal,
    inteiro,
    iter_linhas,
    normalizar_coluna,
    valor,
)
from flowscope.infrastructure.cvm.renda_fixa_securit_filtro import (
    chave_linha as _chave_linha,
)
from flowscope.infrastructure.cvm.renda_fixa_securit_filtro import (
    chaves_alvo as _chaves_alvo,
)
from flowscope.infrastructure.cvm.renda_fixa_securit_filtro import (
    checar_cancelamento as _checar_cancelamento,
)
from flowscope.infrastructure.cvm.renda_fixa_securit_filtro import (
    classe_csv as _classe_csv,
)
from flowscope.infrastructure.cvm.renda_fixa_securit_filtro import (
    cnpj_normalizado as _cnpj,
)
from flowscope.infrastructure.cvm.renda_fixa_securit_filtro import (
    linhas_contendo as _linhas_contendo,
)

#: Fontes registradas por tipo de SECURIT.
FONTE_CRI = "SECURIT_CRI"
FONTE_CRA = "SECURIT_CRA"

#: Campos copiados do SECURIT para o título enriquecido.
_CAMPOS_ENRIQUECIMENTO = (
    "emissor_legal",
    "cnpj_emissor",
    "devedor",
    "cnpj_devedor",
    "garantias",
    "coobrigacao",
    "lastro",
    "sobrecolateralizacao",
    "subordinacao",
    "situacao",
    "rating",
    "contingencias",
    "impacto",
    "desempenho",
    "ltv",
    "data_ltv",
)


@dataclass(frozen=True)
class _Registro:
    """Dados acumulados de um CRI/CRA entre os CSVs do SECURIT."""

    tipo: TipoTitulo
    chave: str = ""
    referencia: date | None = None
    versao: int = 0
    codigo_cetip: str | None = None
    codigo_isin: str | None = None
    identificacao: str | None = None
    cnpj_emissor: str | None = None
    emissor_legal: str | None = None
    cnpj_devedor: str | None = None
    devedor: str | None = None
    serie: str | None = None
    data_emissao: date | None = None
    data_vencimento: date | None = None
    indexador: str | None = None
    taxa: str | None = None
    quantidade: object = None
    valor: object = None
    saldo_devedor: object = None
    valor_posicao: object = None
    garantias: str | None = None
    coobrigacao: str | None = None
    lastro: str | None = None
    sobrecolateralizacao: str | None = None
    subordinacao: str | None = None
    situacao: str | None = None
    rating: str | None = None
    contingencias: str | None = None
    impacto: str | None = None
    desempenho: str | None = None
    ltv: object = None
    data_ltv: date | None = None


def parse_securit_csvs(
    csvs: Mapping[str, bytes],
    tipo: TipoTitulo,
    arquivo: str = "",
    hash_fonte: str = "",
    *,
    codigos_alvo: Iterable[str] | None = None,
    cnpjs_alvo: Iterable[str] | None = None,
    cancelar: Callable[[], None] | None = None,
) -> list[TituloRendaFixa]:
    """Normaliza os CSVs do SECURIT em títulos de um tipo (CRI ou CRA).

    Quando ``codigos_alvo``/``cnpjs_alvo`` são informados, apenas os títulos
    ligados ao ticker são materializados; os demais são descartados antes da
    extração custosa dos campos.
    """
    chaves_alvo, aliases = _preparar_filtro(
        csvs, tipo, codigos_alvo, cnpjs_alvo, cancelar
    )
    if chaves_alvo is not None and not chaves_alvo:
        return []
    registros = _coletar(csvs, tipo, chaves_alvo, aliases, cancelar)
    return [
        _para_titulo(registro, arquivo, hash_fonte)
        for registro in registros.values()
        if registro.chave
    ]


def _preparar_filtro(
    csvs: Mapping[str, bytes],
    tipo: TipoTitulo,
    codigos_alvo: Iterable[str] | None,
    cnpjs_alvo: Iterable[str] | None,
    cancelar: Callable[[], None] | None,
) -> tuple[set[str] | None, set[str]]:
    """Resolve as chaves e aliases do filtro, ou ``None`` para parse completo."""
    if codigos_alvo is None and cnpjs_alvo is None:
        return None, set()
    return _chaves_alvo(csvs, tipo, codigos_alvo, cnpjs_alvo, cancelar)


def _coletar(
    csvs: Mapping[str, bytes],
    tipo: TipoTitulo,
    chaves_alvo: set[str] | None,
    aliases: set[str],
    cancelar: Callable[[], None] | None,
) -> dict[str, _Registro]:
    """Percorre os CSVs e acumula os registros do tipo."""
    registros: dict[str, _Registro] = {}
    for nome in sorted(csvs):
        classe = _classe_csv(nome)
        if classe is None:
            continue
        linhas = _linhas_do_csv(csvs[nome], chaves_alvo, aliases, cancelar)
        _acumular_linhas(registros, linhas, classe, tipo, chaves_alvo, cancelar)
    return registros


def _linhas_do_csv(
    conteudo: bytes,
    chaves_alvo: set[str] | None,
    aliases: set[str],
    cancelar: Callable[[], None] | None,
) -> Iterable:
    """Escolhe entre a leitura completa e a leitura filtrada do CSV."""
    if chaves_alvo is None:
        return iter_linhas(conteudo)
    return _linhas_contendo(conteudo, aliases, cancelar)


def _acumular_linhas(
    registros: dict[str, _Registro],
    linhas: Iterable,
    classe: str,
    tipo: TipoTitulo,
    chaves_alvo: set[str] | None,
    cancelar: Callable[[], None] | None,
) -> None:
    """Acumula as linhas de um CSV, aplicando o filtro quando configurado."""
    for indice, linha in enumerate(linhas):
        _checar_cancelamento(cancelar, indice)
        if chaves_alvo is not None and _chave_linha(linha, tipo) not in chaves_alvo:
            continue
        _acumular(registros, linha, classe, tipo)


def _acumular(
    registros: dict[str, _Registro],
    linha: dict[str, str],
    classe: str,
    tipo: TipoTitulo,
) -> None:
    """Acumula uma linha de CSV no registro da chave correspondente."""
    chave = _chave_linha(linha, tipo)
    if not chave:
        return
    referencia = data(linha, "Data_Referencia")
    versao = inteiro(linha, "Versao")
    atual = registros.get(chave)
    if atual is not None and not _mais_recente(referencia, versao, atual):
        return
    base = atual if atual is not None else _Registro(tipo=tipo, chave=chave)
    registros[chave] = _atualizar(base, linha, classe, referencia, versao, chave)


def _atualizar(
    base: _Registro,
    linha: dict[str, str],
    classe: str,
    referencia: date | None,
    versao: int,
    chave: str,
) -> _Registro:
    """Atualiza o registro com os campos presentes na linha."""
    dados = _campos_comuns(linha, classe)
    if classe == "cedente_devedor":
        dados.update(_campos_devedor(linha))
    return replace(
        base,
        chave=chave,
        referencia=referencia or base.referencia,
        versao=max(versao, base.versao),
        **dados,
    )


def _campos_comuns(linha: dict[str, str], classe: str) -> dict:
    """Extrai os campos presentes em qualquer classe de CSV do SECURIT."""
    dados = {
        "codigo_cetip": codigo_cetip(valor(linha, "Codigo_CETIP", "CETIP")),
        "codigo_isin": codigo_cetip(valor(linha, "Codigo_ISIN", "ISIN")),
        "identificacao": valor(
            linha, "Codigo_Identificacao_Certificado", "Codigo_Identificacao"
        ),
        "cnpj_emissor": _cnpj(valor(linha, "CNPJ_Emissora", "CNPJ_Emissor")),
        "emissor_legal": valor(linha, "Nome_Emissor", "Nome_Emissora", "Emissor"),
        "serie": valor(linha, "Serie", "Numero_Serie"),
        "data_emissao": data(linha, "Data_Emissao"),
        "data_vencimento": data(linha, "Data_Vencimento"),
        "indexador": valor(linha, "Indexador", "Indice"),
        "taxa": valor(linha, "Taxa", "Taxa_Juros"),
        "quantidade": decimal(linha, "Quantidade", "Quantidade_Emitida"),
        "valor": decimal(linha, "Valor_Emissao", "Valor"),
        "saldo_devedor": decimal(linha, "Saldo_Devedor", "Valor_Ativo"),
        "valor_posicao": decimal(linha, "Valor_Posicao", "Valor_Carteira"),
        "situacao": valor(linha, "Situacao", "Situacao_Emissao"),
        "rating": valor(
            linha, "Classificacao_Risco", "Rating", "Nota_Classificacao"
        ),
        "contingencias": valor(linha, "Contingencias", "Contingencia"),
        "impacto": valor(linha, "Impacto", "Impacto_Evento"),
        "desempenho": valor(linha, "Desempenho"),
        "ltv": decimal(linha, "Indice_LTV", "LTV"),
        "data_ltv": data(linha, "Data_LTV"),
    }
    if classe in ("classe", "carteira"):
        dados.update(_campos_classe(linha))
    return {chave: item for chave, item in dados.items() if item is not None}


def _campos_classe(linha: dict[str, str]) -> dict:
    """Extrai garantias, lastro, subordinação e coobrigação."""
    return {
        "garantias": valor(linha, "Garantias", "Garantia"),
        "coobrigacao": valor(linha, "Coobrigacao", "Coobrigação"),
        "lastro": valor(linha, "Lastro", "Direitos_Creditorios"),
        "sobrecolateralizacao": valor(
            linha, "Sobrecolateralizacao", "Sobrecolateralização"
        ),
        "subordinacao": valor(linha, "Subordinacao", "Subordinação"),
    }


def _campos_devedor(linha: dict[str, str]) -> dict:
    """Extrai o devedor econômico apenas de linhas do tipo ``Devedor``."""
    tipo = normalizar_coluna(valor(linha, "Tipo", "Tipo_Parte"))
    if tipo and tipo not in ("devedor", "devedores"):
        return {}
    cnpj = valor(
        linha,
        "CNPJ_Cedente_Devedor",
        "CNPJ_Devedor",
        "CNPJ",
        "CNPJ_Parte",
    )
    nome = valor(
        linha,
        "Nome_Cedente_Devedor",
        "Nome_Devedor",
        "Nome",
        "Razao_Social",
    )
    return {
        "cnpj_devedor": _cnpj(cnpj),
        "devedor": nome,
    }


def _mais_recente(
    referencia: date | None, versao: int, atual: _Registro
) -> bool:
    """Indica se a linha é tão ou mais recente que o registro acumulado."""
    if referencia is not None and atual.referencia is not None:
        if referencia != atual.referencia:
            return referencia > atual.referencia
    elif referencia is not None and atual.referencia is None:
        return True
    return versao >= atual.versao


def _para_titulo(
    registro: _Registro, arquivo: str, hash_fonte: str
) -> TituloRendaFixa:
    """Monta o título de domínio a partir do registro acumulado."""
    return TituloRendaFixa(
        tipo=registro.tipo,
        papel=PapelTitulo.OBRIGACAO,
        id=id_curto(registro.chave),
        chave_fonte=registro.chave,
        rotulo=registro.identificacao or registro.tipo.rotulo,
        emissor_legal=registro.emissor_legal,
        cnpj_emissor=registro.cnpj_emissor,
        devedor=registro.devedor,
        cnpj_devedor=registro.cnpj_devedor,
        identificacao=registro.identificacao,
        codigos=tuple(
            codigo
            for codigo in (
                registro.codigo_cetip,
                registro.codigo_isin,
                registro.identificacao,
            )
            if codigo
        ),
        serie=registro.serie,
        data_emissao=registro.data_emissao,
        data_vencimento=registro.data_vencimento,
        indexador=registro.indexador,
        taxa=registro.taxa,
        quantidade=registro.quantidade,
        valor=registro.valor,
        saldo_devedor=registro.saldo_devedor,
        valor_posicao=registro.valor_posicao,
        garantias=registro.garantias,
        coobrigacao=registro.coobrigacao,
        lastro=registro.lastro,
        sobrecolateralizacao=registro.sobrecolateralizacao,
        subordinacao=registro.subordinacao,
        situacao=registro.situacao,
        rating=registro.rating,
        contingencias=registro.contingencias,
        impacto=registro.impacto,
        desempenho=registro.desempenho,
        ltv=registro.ltv,
        data_ltv=registro.data_ltv,
        fonte=FONTE_CRI if registro.tipo is TipoTitulo.CRI else FONTE_CRA,
        data_referencia=registro.referencia,
        arquivo=arquivo,
        hash_fonte=hash_fonte,
    )


