"""Quantidade de acionistas de companhias abertas via FRE + FCA (CVM).

Resolve o CNPJ da companhia a partir do ticker usando o Formulário Cadastral
(FCA, ``fca_cia_aberta_valor_mobiliario``) e a quantidade de acionistas no
Formulário de Referência (FRE, ``fre_cia_aberta_distribuicao_capital``),
selecionando a versão mais recente. Os arquivos anuais são cacheados pelo
``CvmDatasetDownloader`` e as informações normalizadas (mapa ticker→CNPJ e
quantidade por CNPJ) são cacheadas por hash do arquivo de origem e versão do
parser.
"""

import csv
import io
import logging
from collections.abc import Callable
from datetime import date

from flowscope.domain.cvm import normalizar_cnpj
from flowscope.infrastructure.cache import CacheManager
from flowscope.infrastructure.cvm.datasets import CvmDatasetDownloader, hash_sha256

logger = logging.getLogger("flowscope")

#: Fonte registrada nos valores produzidos por este adaptador.
FONTE_CVM_ACIONISTAS = "CVM"

#: Diretórios oficiais dos dados abertos da CVM.
FRE_BASE_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FRE/DADOS"
FCA_BASE_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS"

#: Versão do parser, usada para invalidar o cache normalizado.
PARSER_VERSION = "cvm-acionistas-v1"

#: Prefixo do CSV de distribuição de capital no ZIP do FRE.
_ARQUIVO_FRE = "fre_cia_aberta_distribuicao_capital"
#: Prefixo do CSV de valores mobiliários no ZIP do FCA.
_ARQUIVO_FCA = "fca_cia_aberta_valor_mobiliario"

#: Quantidade de anos consultados para trás a partir da referência.
_ANOS_JANELA = 2


def _arquivo_fre(ano: int) -> str:
    """Retorna o nome do ZIP anual do FRE."""
    return f"fre_cia_aberta_{ano}.zip"


def _arquivo_fca(ano: int) -> str:
    """Retorna o nome do ZIP anual do FCA."""
    return f"fca_cia_aberta_{ano}.zip"


def parse_valor_mobiliario(conteudo: bytes) -> dict[str, str]:
    """Mapeia ``Codigo_Negociacao`` (ticker) para o CNPJ normalizado."""
    mapa: dict[str, str] = {}
    for linha in _ler_csv(conteudo):
        ticker = _texto(linha.get("Codigo_Negociacao"))
        cnpj = normalizar_cnpj(linha.get("CNPJ_Companhia"))
        if ticker and cnpj:
            mapa.setdefault(ticker.strip().upper(), cnpj)
    return mapa


def parse_distribuicao_capital(conteudo: bytes) -> dict[str, int]:
    """Mapeia CNPJ normalizado para a quantidade total de acionistas.

    Soma pessoa física, pessoa jurídica e investidores institucionais,
    selecionando o registro de maior ``Versao`` por CNPJ, sem filtrar pela
    ``Data_Referencia`` (que pode ser futura).
    """
    registros: dict[str, tuple[int, int]] = {}
    for linha in _ler_csv(conteudo):
        cnpj = normalizar_cnpj(linha.get("CNPJ_Companhia"))
        if not cnpj:
            continue
        total = _somar_acionistas(linha)
        versao = _inteiro(linha.get("Versao"))
        atual = registros.get(cnpj)
        if atual is None or versao >= atual[0]:
            registros[cnpj] = (versao, total)
    return {cnpj: total for cnpj, (_, total) in registros.items()}


def _somar_acionistas(linha: dict[str, str]) -> int:
    """Soma as quantidades de acionistas PF, PJ e institucionais."""
    return (
        _inteiro(linha.get("Quantidade_Acionistas_PF"))
        + _inteiro(linha.get("Quantidade_Acionistas_PJ"))
        + _inteiro(linha.get("Quantidade_Acionistas_Investidores_Institucionais"))
    )


def _ler_csv(conteudo: bytes) -> list[dict[str, str]]:
    """Lê o CSV da CVM (latin1, delimitador ``;``) como lista de dicionários."""
    texto = conteudo.decode("latin1")
    leitor = csv.DictReader(io.StringIO(texto), delimiter=";")
    if leitor.fieldnames is None:
        return []
    return [linha for linha in leitor]


def _texto(valor: object) -> str | None:
    """Retorna o texto de um valor, ou ``None`` quando vazio."""
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None


def _inteiro(valor: object) -> int:
    """Interpreta um valor como inteiro, retornando zero quando inválido."""
    try:
        return int(str(valor).strip())
    except (TypeError, ValueError):
        return 0


class CvmAcionistasSource:
    """Resolve a quantidade de acionistas de um ticker via FRE + FCA."""

    def __init__(
        self: "CvmAcionistasSource",
        downloader_fre: CvmDatasetDownloader | None = None,
        downloader_fca: CvmDatasetDownloader | None = None,
        cache: CacheManager | None = None,
        parser_version: str = PARSER_VERSION,
        anos_janela: int = _ANOS_JANELA,
    ) -> None:
        """Inicializa a fonte com downloaders, cache e versão do parser."""
        self._downloader_fre = downloader_fre or _criar_downloader_fre()
        self._downloader_fca = downloader_fca or _criar_downloader_fca()
        self._cache = cache or CacheManager()
        self._parser_version = parser_version
        self._anos_janela = anos_janela

    def obter_acionistas(
        self: "CvmAcionistasSource", ticker: str, reference_date: date
    ) -> int | None:
        """Retorna a quantidade de acionistas, ou ``None`` quando indisponível."""
        try:
            cnpj = self._resolver_cnpj(ticker, reference_date)
            if cnpj is None:
                return None
            return self._quantidade(cnpj, reference_date)
        except Exception:  # aquisição tolerante por ticker
            logger.warning("Falha ao obter acionistas de %s", ticker, exc_info=True)
            return None

    def obter_cnpj(
        self: "CvmAcionistasSource", ticker: str, reference_date: date
    ) -> str | None:
        """Retorna o CNPJ da companhia resolvido no FCA, ou ``None``."""
        try:
            return self._resolver_cnpj(ticker, reference_date)
        except Exception:  # aquisição tolerante por ticker
            logger.warning("Falha ao resolver CNPJ de %s", ticker, exc_info=True)
            return None

    def _resolver_cnpj(
        self: "CvmAcionistasSource", ticker: str, reference_date: date
    ) -> str | None:
        """Resolve o CNPJ do ticker no FCA, do ano mais recente para o mais antigo."""
        chave = ticker.strip().upper()
        for ano in self._anos(reference_date):
            mapa = self._mapa(
                self._downloader_fca, _ARQUIVO_FCA, "fca", ano, parse_valor_mobiliario
            )
            cnpj = mapa.get(chave)
            if cnpj is not None:
                return cnpj
        return None

    def _quantidade(
        self: "CvmAcionistasSource", cnpj: str, reference_date: date
    ) -> int | None:
        """Busca a quantidade de acionistas do CNPJ no FRE."""
        for ano in self._anos(reference_date):
            mapa = self._mapa(
                self._downloader_fre,
                _ARQUIVO_FRE,
                "fre",
                ano,
                parse_distribuicao_capital,
            )
            if cnpj in mapa:
                return mapa[cnpj]
        return None

    def _anos(self: "CvmAcionistasSource", reference_date: date) -> list[int]:
        """Retorna os anos a consultar, do mais recente para o mais antigo."""
        return [reference_date.year - i for i in range(self._anos_janela)]

    def _mapa(
        self: "CvmAcionistasSource",
        downloader: CvmDatasetDownloader,
        prefixo: str,
        dataset: str,
        ano: int,
        parser: Callable[[bytes], dict],
    ) -> dict:
        """Retorna o mapa normalizado do ano, usando o cache por hash do arquivo."""
        data = downloader.baixar_ano(ano)
        digest = hash_sha256(data)
        chave = self._chave(dataset, ano, digest)
        cacheado = self._cache.read_meta(chave)
        if (
            cacheado is not None
            and cacheado.get("sha256") == digest
            and cacheado.get("parser_version") == self._parser_version
            and isinstance(cacheado.get("data"), dict)
        ):
            return cacheado["data"]
        csvs = downloader.extrair_csvs(data, ano)
        conteudo = _csv_alvo(csvs, prefixo)
        mapa = parser(conteudo) if conteudo is not None else {}
        self._cache.write_meta(
            chave,
            {
                "sha256": digest,
                "parser_version": self._parser_version,
                "data": mapa,
            },
        )
        return mapa

    def _chave(
        self: "CvmAcionistasSource", dataset: str, ano: int, digest: str
    ) -> str:
        """Monta a chave de cache normalizado, ligada ao hash e à versão do parser."""
        return (
            f"cvm_acionistas_{dataset}_{ano}_{digest[:16]}_{self._parser_version}"
        )


def _csv_alvo(csvs: dict[str, bytes], prefixo: str) -> bytes | None:
    """Retorna o conteúdo do CSV cujo nome contém o prefixo informado."""
    for nome, conteudo in csvs.items():
        if prefixo in nome:
            return conteudo
    return None


def _criar_downloader_fre() -> CvmDatasetDownloader:
    """Cria o downloader anual do FRE."""
    return CvmDatasetDownloader(
        base_url=FRE_BASE_URL,
        arquivo=_arquivo_fre,
        dataset="fre",
        parser_version=PARSER_VERSION,
    )


def _criar_downloader_fca() -> CvmDatasetDownloader:
    """Cria o downloader anual do FCA."""
    return CvmDatasetDownloader(
        base_url=FCA_BASE_URL,
        arquivo=_arquivo_fca,
        dataset="fca",
        parser_version=PARSER_VERSION,
    )
