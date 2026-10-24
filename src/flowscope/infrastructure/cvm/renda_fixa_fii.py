"""Parsers da carteira de renda fixa dos FIIs (INF_TRIMESTRAL e INF_MENSAL)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from flowscope.domain.cvm import normalizar_cnpj
from flowscope.domain.renda_fixa import (
    PapelTitulo,
    TipoTitulo,
    TituloAgregado,
    TituloRendaFixa,
    chave_fii,
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

#: Fontes registradas nos direitos de FII.
FONTE_TRIMESTRAL = "FII_INF_TRIMESTRAL"
FONTE_MENSAL = "FII_INF_MENSAL"

#: Prefixos dos CSVs usados na aquisição.
CSV_TRIMESTRAL = "inf_trimestral_fii_ativo"
CSV_MENSAL = "inf_mensal_fii_ativo_passivo"

#: Tipos de renda fixa aceitos na carteira de FII.
_TIPOS = (
    (("recebiveis imobiliarios", "cri"), TipoTitulo.CRI),
    (("recebiveis do agronegocio", "cra"), TipoTitulo.CRA),
    (("letra de credito imobiliario", "lci"), TipoTitulo.LCI),
    (("letra de credito do agronegocio", "lca"), TipoTitulo.LCA),
)


@dataclass(frozen=True)
class _Registro:
    """Posição candidata da carteira trimestral do FII."""

    titulo: TituloRendaFixa
    referencia: date | None
    versao: int


def tipo_direito(valor_ativo: str | None) -> TipoTitulo | None:
    """Classifica o tipo do ativo da carteira de FII."""
    texto = normalizar_coluna(valor_ativo)
    for termos, tipo in _TIPOS:
        if any(normalizar_coluna(termo) in texto for termo in termos):
            return tipo
    return None


def parse_fii_ativo(
    conteudo: bytes,
    cnpj: str,
    arquivo: str = "",
    hash_fonte: str = "",
) -> list[TituloRendaFixa]:
    """Extrai as posições de CRI/CRA e LCI/LCA do informe trimestral do FII."""
    alvo = normalizar_cnpj(cnpj)
    if not alvo:
        return []
    selecionados: dict[str, _Registro] = {}
    for linha in iter_linhas(conteudo):
        if normalizar_cnpj(
            valor(linha, "CNPJ_Fundo_Classe", "CNPJ_Fundo")
        ) != alvo:
            continue
        tipo = tipo_direito(
            valor(linha, "Tipo_Ativo", "Tipo", "Classe", "Tipo_Papel")
        )
        if tipo is None:
            continue
        titulo = _titulo(linha, tipo, arquivo, hash_fonte)
        registro = _Registro(
            titulo, data(linha, "Data_Referencia"), inteiro(linha, "Versao")
        )
        chave = chave_posicao_fii(titulo)
        atual = selecionados.get(chave)
        if atual is None or _mais_recente(registro, atual):
            selecionados[chave] = registro
    return [registro.titulo for registro in selecionados.values()]


def parse_fii_ativo_passivo(
    conteudo: bytes, cnpj: str
) -> list[TituloAgregado]:
    """Extrai os agregados de debêntures e CDB da última data/versão do FII."""
    alvo = normalizar_cnpj(cnpj)
    if not alvo:
        return []
    melhor = _melhor_linha(conteudo, alvo)
    if melhor is None:
        return []
    referencia = data(melhor, "Data_Referencia")
    agregados: list[TituloAgregado] = []
    for coluna, tipo in (
        ("Debentures", TipoTitulo.DEBENTURE),
        ("Certificados_Deposito_Valores_Mobiliarios", TipoTitulo.CDB),
    ):
        valor_total = decimal(melhor, coluna)
        if valor_total is None or valor_total <= Decimal(0):
            continue
        agregados.append(
            TituloAgregado(
                tipo=tipo,
                papel=PapelTitulo.DIREITO,
                valor=valor_total,
                fonte=FONTE_MENSAL,
                data_referencia=referencia,
            )
        )
    return agregados


def _melhor_linha(conteudo: bytes, alvo: str) -> dict[str, str] | None:
    """Seleciona a linha do fundo na maior data de referência e versão."""
    melhor: dict[str, str] | None = None
    chave: tuple[date, int] | None = None
    for linha in iter_linhas(conteudo):
        if normalizar_cnpj(
            valor(linha, "CNPJ_Fundo_Classe", "CNPJ_Fundo")
        ) != alvo:
            continue
        referencia = data(linha, "Data_Referencia")
        versao = inteiro(linha, "Versao")
        candidata = (referencia or date.min, versao)
        if chave is None or candidata >= chave:
            melhor, chave = linha, candidata
    return melhor


def _titulo(
    linha: dict[str, str],
    tipo: TipoTitulo,
    arquivo: str,
    hash_fonte: str,
) -> TituloRendaFixa:
    """Normaliza uma posição da carteira do FII em ``TituloRendaFixa``."""
    emissor = valor(linha, "Emissor", "Nome_Emissor")
    codigo = valor(linha, "Codigo_CETIP", "CETIP") or codigo_cetip(emissor)
    cnpj_emissor = normalizar_cnpj(
        valor(linha, "CNPJ_Emissor", "CNPJ_Emissora") or ""
    )
    emissao = valor(linha, "Emissao")
    serie = valor(linha, "Serie")
    vencimento = data(linha, "Data_Vencimento")
    chave = chave_fii(codigo, cnpj_emissor, emissao, serie, vencimento)
    nome = valor(linha, "Nome_Ativo", "Nome")
    return TituloRendaFixa(
        tipo=tipo,
        papel=PapelTitulo.DIREITO,
        id=id_curto(chave),
        chave_fonte=chave,
        rotulo=nome or emissor or tipo.rotulo,
        emissor_legal=emissor,
        cnpj_emissor=cnpj_emissor or None,
        identificacao=codigo or nome,
        codigos=(codigo,) if codigo else (),
        emissao=emissao,
        serie=serie,
        data_vencimento=vencimento,
        indexador=valor(linha, "Indexador"),
        taxa=valor(linha, "Taxa"),
        quantidade=decimal(linha, "Quantidade"),
        valor=decimal(linha, "Valor"),
        valor_posicao=decimal(linha, "Valor_Posicao", "Valor_Atual"),
        fonte=FONTE_TRIMESTRAL,
        data_referencia=data(linha, "Data_Referencia"),
        arquivo=arquivo,
        hash_fonte=hash_fonte,
    )


def chave_posicao_fii(titulo: TituloRendaFixa) -> str:
    """Deriva a identidade estável da posição entre versões do informe.

    O código CETIP pode estar ausente em versões antigas e presente nas mais
    recentes. A identidade por emissor/emissão/série/vencimento evita que a
    mesma posição apareça duplicada quando o código passa a ser informado.
    """
    if titulo.cnpj_emissor and (
        titulo.emissao or titulo.serie or titulo.data_vencimento
    ):
        return chave_fii(
            None,
            titulo.cnpj_emissor,
            titulo.emissao,
            titulo.serie,
            titulo.data_vencimento,
        )
    return titulo.chave_fonte


def _mais_recente(candidato: _Registro, atual: _Registro) -> bool:
    """Compara data de referência e versão das posições do FII."""
    if candidato.referencia != atual.referencia:
        datas = [item for item in (candidato.referencia, atual.referencia) if item]
        return bool(datas) and candidato.referencia == max(datas)
    return candidato.versao >= atual.versao
