"""Parser das obrigações de renda fixa do Formulário de Referência (FRE)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from flowscope.domain.cvm import normalizar_cnpj
from flowscope.domain.renda_fixa import (
    PapelTitulo,
    TipoTitulo,
    TituloRendaFixa,
    chave_fonte,
    chave_fre,
    id_curto,
)
from flowscope.infrastructure.cvm.renda_fixa_common import (
    data,
    decimal,
    inteiro,
    iter_linhas,
    normalizar_coluna,
    valor,
)

#: Fonte registrada nos títulos originados do FRE.
FONTE = "FRE"

#: Prefixo do CSV de outros valores mobiliários no ZIP do FRE.
CSV_PREFIXO = "fre_cia_aberta_outro_valor_mobiliario"

#: Tipos de renda fixa aceitos no campo ``Valor_Mobiliario``.
_TIPOS = (
    (("convers",), TipoTitulo.DEBENTURE_CONVERSIVEL),
    (("nota comercial", "commercial paper"), TipoTitulo.NOTA_COMERCIAL),
    (("recebiveis imobiliarios", "cri"), TipoTitulo.CRI),
    (("recebiveis do agronegocio", "cra"), TipoTitulo.CRA),
    (("lci", "letra de credito imobiliario"), TipoTitulo.LCI),
    (("lca", "letra de credito do agronegocio"), TipoTitulo.LCA),
    (("cdb", "certificado de deposito bancario"), TipoTitulo.CDB),
    (("letra financeira",), TipoTitulo.LETRA_FINANCEIRA),
    (("debenture",), TipoTitulo.DEBENTURE),
)


@dataclass(frozen=True)
class _Registro:
    """Linha candidata do FRE com a chave de seleção da versão mais recente."""

    titulo: TituloRendaFixa
    referencia: date | None
    versao: int


def tipo_renda_fixa(valor_mobiliario: str | None) -> TipoTitulo | None:
    """Classifica o ``Valor_Mobiliario`` do FRE em um tipo de renda fixa."""
    texto = normalizar_coluna(valor_mobiliario)
    for termos, tipo in _TIPOS:
        if any(normalizar_coluna(termo) in texto for termo in termos):
            return tipo
    return None


def parse_fre(
    conteudo: bytes,
    cnpj: str,
    arquivo: str = "",
    hash_fonte: str = "",
) -> list[TituloRendaFixa]:
    """Extrai os títulos de renda fixa do CNPJ, selecionando a versão mais recente."""
    alvo = normalizar_cnpj(cnpj)
    if not alvo:
        return []
    selecionados: dict[str, _Registro] = {}
    for linha in iter_linhas(conteudo):
        if normalizar_cnpj(valor(linha, "CNPJ_Companhia", "CNPJ")) != alvo:
            continue
        tipo = tipo_renda_fixa(valor(linha, "Valor_Mobiliario"))
        if tipo is None:
            continue
        titulo = _titulo(linha, tipo, arquivo, hash_fonte)
        registro = _Registro(
            titulo,
            data(linha, "Data_Referencia"),
            inteiro(linha, "Versao"),
        )
        identidade = _identidade(titulo)
        atual = selecionados.get(identidade)
        if atual is None or _mais_recente(registro, atual):
            selecionados[identidade] = registro
    return [registro.titulo for registro in selecionados.values()]


def _identidade(titulo: TituloRendaFixa) -> str:
    """Deriva a identidade estável usada para escolher a versão mais recente."""
    return chave_fonte(
        (
            titulo.tipo.value,
            titulo.identificacao or "",
            titulo.data_emissao.isoformat() if titulo.data_emissao else "",
            titulo.data_vencimento.isoformat() if titulo.data_vencimento else "",
            titulo.serie or "",
        )
    )


def _mais_recente(candidato: _Registro, atual: _Registro) -> bool:
    """Compara data de referência e versão para escolher a reapresentação."""
    if candidato.referencia != atual.referencia:
        datas = (candidato.referencia, atual.referencia)
        preenchidas = [item for item in datas if item is not None]
        return bool(preenchidas) and candidato.referencia == max(preenchidas)
    return candidato.versao > atual.versao


def _titulo(
    linha: dict[str, str],
    tipo: TipoTitulo,
    arquivo: str,
    hash_fonte: str,
) -> TituloRendaFixa:
    """Normaliza uma linha do FRE em ``TituloRendaFixa``."""
    cnpj = normalizar_cnpj(valor(linha, "CNPJ_Companhia", "CNPJ"))
    identificacao = valor(
        linha,
        "Identificacao_Valor_Mobiliario",
        "Identificacao",
        "Codigo_Identificacao",
    )
    data_emissao = data(linha, "Data_Emissao")
    data_vencimento = data(linha, "Data_Vencimento")
    quantidade = decimal(linha, "Quantidade")
    valor_titulo = decimal(linha, "Valor")
    chave = chave_fre(
        cnpj,
        tipo.value,
        identificacao or "",
        data_emissao,
        data_vencimento,
        quantidade,
        valor_titulo,
    )
    referencia = data(linha, "Data_Referencia")
    caracteristicas = valor(linha, "Caracteristicas_Divida")
    restricao = valor(linha, "Restricao_Circulacao")
    return TituloRendaFixa(
        tipo=tipo,
        papel=PapelTitulo.OBRIGACAO,
        id=id_curto(chave),
        chave_fonte=chave,
        rotulo=identificacao or tipo.rotulo,
        devedor="Companhia" if tipo in (TipoTitulo.CRI, TipoTitulo.CRA) else None,
        cnpj_devedor=(
            cnpj if tipo in (TipoTitulo.CRI, TipoTitulo.CRA) else None
        ),
        identificacao=identificacao,
        serie=valor(linha, "Serie"),
        data_emissao=data_emissao,
        data_vencimento=data_vencimento,
        indexador=valor(linha, "Indexador"),
        taxa=valor(linha, "Taxa"),
        quantidade=quantidade,
        valor=valor_titulo,
        saldo_devedor=decimal(linha, "Saldo_Devedor"),
        caracteristicas=_juntar(caracteristicas, restricao),
        condicao_alteracao=valor(linha, "Condicao_Alteracao_Direitos"),
        fonte=FONTE,
        data_referencia=referencia,
        arquivo=arquivo,
        hash_fonte=hash_fonte,
    )


def _juntar(*partes: str | None) -> str | None:
    """Junta textos não vazios separados por ponto e vírgula."""
    texto = "; ".join(parte for parte in partes if parte)
    return texto or None
