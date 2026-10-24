"""Carga e normalização dos datasets CVM usados na renda fixa."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import date

from flowscope.domain.renda_fixa import (
    FonteTitulos,
    TipoTitulo,
    TituloAgregado,
    TituloRendaFixa,
)
from flowscope.infrastructure.cvm.datasets import (
    CvmDatasetDownloader,
    hash_sha256,
)
from flowscope.infrastructure.cvm.renda_fixa_common import melhor_por_chave
from flowscope.infrastructure.cvm.renda_fixa_fii import (
    CSV_MENSAL,
    CSV_TRIMESTRAL,
    chave_posicao_fii,
    parse_fii_ativo,
    parse_fii_ativo_passivo,
)
from flowscope.infrastructure.cvm.renda_fixa_fre import (
    CSV_PREFIXO as CSV_FRE,
)
from flowscope.infrastructure.cvm.renda_fixa_fre import parse_fre
from flowscope.infrastructure.cvm.renda_fixa_securit import parse_securit_csvs


def carregar_fre(
    downloader: CvmDatasetDownloader,
    cnpj: str,
    anos: list[int],
    fontes: dict[str, FonteTitulos],
    cancelar: Callable[[], None] | None = None,
) -> list[TituloRendaFixa]:
    """Lê o FRE de todos os anos e seleciona a versão mais recente por título."""
    itens: list[TituloRendaFixa] = []
    arquivos: list[str] = []
    digests: list[str] = []
    for ano in anos:
        checar(cancelar)
        _dados, digest, csvs = _carregar_ano(downloader, ano)
        for nome, conteudo in csvs.items():
            if CSV_FRE not in nome:
                continue
            itens.extend(
                parse_fre(conteudo, cnpj, arquivo=nome, hash_fonte=digest)
            )
            arquivos.append(nome)
            digests.append(digest)
    if arquivos:
        fontes["fre"] = FonteTitulos(
            data_referencia=_maior_referencia(itens),
            arquivo="; ".join(arquivos),
            hash="; ".join(dict.fromkeys(digests)),
        )
    return melhor_por_chave(itens)


def carregar_fii_ativo(
    downloader: CvmDatasetDownloader,
    cnpj: str,
    anos: list[int],
    fontes: dict[str, FonteTitulos],
    cancelar: Callable[[], None] | None = None,
) -> list[TituloRendaFixa]:
    """Lê a carteira trimestral do FII, usando a última data/versão."""
    itens: list[TituloRendaFixa] = []
    arquivos: list[str] = []
    digests: list[str] = []
    for ano in anos:
        checar(cancelar)
        _dados, digest, csvs = _carregar_ano(downloader, ano)
        for nome, conteudo in csvs.items():
            if CSV_TRIMESTRAL not in nome:
                continue
            itens.extend(
                parse_fii_ativo(conteudo, cnpj, arquivo=nome, hash_fonte=digest)
            )
            arquivos.append(nome)
            digests.append(digest)
    if arquivos:
        fontes["fii_ativo"] = FonteTitulos(
            data_referencia=_maior_referencia(itens),
            arquivo="; ".join(arquivos),
            hash="; ".join(dict.fromkeys(digests)),
        )
    return melhor_por_chave(itens, chave=chave_posicao_fii)


def carregar_fii_passivo(
    downloader: CvmDatasetDownloader,
    cnpj: str,
    anos: list[int],
    fontes: dict[str, FonteTitulos],
    cancelar: Callable[[], None] | None = None,
) -> list[TituloAgregado]:
    """Lê os agregados mensais do FII, usando a última data/versão."""
    melhores: dict[str, TituloAgregado] = {}
    arquivos: list[str] = []
    digests: list[str] = []
    for ano in anos:
        checar(cancelar)
        _dados, digest, csvs = _carregar_ano(downloader, ano)
        for nome, conteudo in csvs.items():
            if CSV_MENSAL not in nome:
                continue
            for item in parse_fii_ativo_passivo(conteudo, cnpj):
                atual = melhores.get(item.tipo.value)
                if atual is None or _ref(item) > _ref(atual):
                    melhores[item.tipo.value] = item
            arquivos.append(nome)
            digests.append(digest)
    itens = list(melhores.values())
    if arquivos:
        fontes["fii_mensal"] = FonteTitulos(
            data_referencia=_maior_referencia(itens),
            arquivo="; ".join(arquivos),
            hash="; ".join(dict.fromkeys(digests)),
        )
    return itens


def carregar_securit(
    downloader: CvmDatasetDownloader,
    tipo: TipoTitulo,
    anos: list[int],
    chave_fonte: str,
    fontes: dict[str, FonteTitulos],
    codigos: set[str],
    cnpjs: set[str],
    cancelar: Callable[[], None] | None = None,
) -> list[TituloRendaFixa]:
    """Lê os CSVs do SECURIT e devolve apenas os registros do ticker."""
    itens: list[TituloRendaFixa] = []
    arquivos: list[str] = []
    digests: list[str] = []
    for ano in anos:
        checar(cancelar)
        _dados, digest, csvs = _carregar_ano(downloader, ano)
        if not csvs:
            continue
        itens.extend(
            parse_securit_csvs(
                csvs,
                tipo,
                hash_fonte=digest,
                codigos_alvo=codigos,
                cnpjs_alvo=cnpjs,
                cancelar=cancelar,
            )
        )
        arquivos.extend(csvs)
        digests.append(digest)
    if arquivos:
        fontes[chave_fonte] = FonteTitulos(
            data_referencia=_maior_referencia(itens),
            arquivo="; ".join(arquivos),
            hash="; ".join(dict.fromkeys(digests)),
        )
    return melhor_por_chave(itens)


def anos(reference_date: date, janela: int) -> list[int]:
    """Retorna os anos a consultar, do mais recente para o mais antigo."""
    return [reference_date.year - indice for indice in range(janela)]



def reportar(
    progress: Callable[[int, int, str], None] | None,
    atual: int,
    total: int,
    rotulo: str,
) -> None:
    """Publica o progresso da etapa corrente, quando houver callback."""
    if progress is not None:
        progress(atual, total, rotulo)


def alvos_join(
    obrigacoes: Iterable[TituloRendaFixa],
    direitos: Iterable[TituloRendaFixa],
) -> tuple[set[str], set[str]]:
    """Coleta códigos e CNPJs de devedor dos CRI/CRA do ticker."""
    codigos: set[str] = set()
    cnpjs: set[str] = set()
    for item in (*tuple(obrigacoes), *tuple(direitos)):
        if item.tipo not in (TipoTitulo.CRI, TipoTitulo.CRA):
            continue
        codigos.update(codigo for codigo in item.codigos if codigo)
        if item.identificacao:
            codigos.add(item.identificacao)
        if item.cnpj_devedor:
            cnpjs.add(item.cnpj_devedor)
    return codigos, cnpjs


def checar(cancelar: Callable[[], None] | None) -> None:
    """Propaga o cancelamento cooperativo, quando houver callback."""
    if cancelar is not None:
        cancelar()


def deduplicar(itens: Iterable[TituloRendaFixa]) -> list[TituloRendaFixa]:
    """Remove títulos repetidos por identificador."""
    vistos: dict[str, TituloRendaFixa] = {}
    for item in itens:
        vistos.setdefault(item.id, item)
    return list(vistos.values())


def deduplicar_agregados(
    itens: Iterable[TituloAgregado],
) -> list[TituloAgregado]:
    """Remove agregados repetidos por tipo."""
    vistos: dict[str, TituloAgregado] = {}
    for item in itens:
        vistos.setdefault(item.tipo.value, item)
    return list(vistos.values())


def _carregar_ano(
    downloader: CvmDatasetDownloader, ano: int
) -> tuple[bytes, str, dict[str, bytes]]:
    """Baixa e extrai o ZIP anual, devolvendo dados, hash e CSVs."""
    dados = downloader.baixar_ano(ano)
    return dados, hash_sha256(dados), downloader.extrair_csvs(dados, ano)


def _maior_referencia(itens: Iterable) -> date | None:
    """Seleciona a maior data de referência entre os itens informados."""
    datas = [
        item.data_referencia
        for item in itens
        if getattr(item, "data_referencia", None) is not None
    ]
    return max(datas) if datas else None


def _ref(item: TituloAgregado) -> date:
    """Chave de comparação da data de referência de um agregado."""
    return item.data_referencia or date.min



