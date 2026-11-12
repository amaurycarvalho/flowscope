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
from decimal import Decimal, InvalidOperation

from flowscope.domain.cvm import normalizar_cnpj
from flowscope.domain.renda_fixa import cnpj_valido
from flowscope.infrastructure.cache import CacheManager
from flowscope.infrastructure.cvm.datasets import CvmDatasetDownloader, hash_sha256

logger = logging.getLogger("flowscope")

#: Fonte registrada nos valores produzidos por este adaptador.
FONTE_CVM_ACIONISTAS = "CVM"

#: Diretórios oficiais dos dados abertos da CVM.
FRE_BASE_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FRE/DADOS"
FCA_BASE_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS"
CAD_BASE_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS"

#: Versão do parser, usada para invalidar o cache normalizado.
PARSER_VERSION = "cvm-acionistas-v3"

#: Prefixo do CSV de distribuição de capital no ZIP do FRE.
_ARQUIVO_FRE = "fre_cia_aberta_distribuicao_capital"
#: Prefixo do CSV de valores mobiliários no ZIP do FCA.
_ARQUIVO_FCA = "fca_cia_aberta_valor_mobiliario"
#: Nome do CSV do cadastro de companhias abertas da CVM.
_ARQUIVO_CAD = "cad_cia_aberta.csv"

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


def parse_cadastro_cia(conteudo: bytes) -> dict[str, dict[str, str]]:
    """Mapeia o código CVM para o CNPJ normalizado e a razão social."""
    mapa: dict[str, dict[str, str]] = {}
    for linha in _ler_csv(conteudo):
        codigo = _normalizar_codigo_cvm(_texto(linha.get("CD_CVM")))
        cnpj = normalizar_cnpj(linha.get("CNPJ_CIA"))
        if codigo and cnpj_valido(cnpj):
            mapa.setdefault(
                codigo,
                {
                    "cnpj": cnpj,
                    "razao_social": _texto(linha.get("DENOM_SOCIAL")) or "",
                },
            )
    return mapa


def _normalizar_codigo_cvm(valor: str | None) -> str | None:
    """Remove zeros à esquerda de um código CVM, tolerando vazio."""
    if not valor:
        return None
    normalizado = valor.strip().lstrip("0")
    return normalizado or "0"


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


def parse_acoes_circulacao(conteudo: bytes) -> dict[str, Decimal]:
    """Mapeia CNPJ normalizado para o total de ações em circulação (*free float*).

    Lê ``Quantidade_Total_Acoes_Circulacao`` do mesmo CSV de distribuição de
    capital, selecionando o registro de maior ``Versao`` por CNPJ. Linhas com a
    quantidade ausente ou inválida são ignoradas.
    """
    registros: dict[str, tuple[int, Decimal]] = {}
    for linha in _ler_csv(conteudo):
        cnpj = normalizar_cnpj(linha.get("CNPJ_Companhia"))
        if not cnpj:
            continue
        quantidade = _decimal(linha.get("Quantidade_Total_Acoes_Circulacao"))
        if quantidade is None:
            continue
        versao = _inteiro(linha.get("Versao"))
        atual = registros.get(cnpj)
        if atual is None or versao >= atual[0]:
            registros[cnpj] = (versao, quantidade)
    return {cnpj: quantidade for cnpj, (_, quantidade) in registros.items()}


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


def _decimal(valor: object) -> Decimal | None:
    """Interpreta um valor como ``Decimal``, ou ``None`` quando vazio/inválido."""
    texto = _texto(valor)
    if texto is None:
        return None
    try:
        return Decimal(texto)
    except (InvalidOperation, ValueError):
        return None


class CvmAcionistasSource:
    """Resolve a quantidade de acionistas de um ticker via FRE + FCA."""

    def __init__(
        self: "CvmAcionistasSource",
        downloader_fre: CvmDatasetDownloader | None = None,
        downloader_fca: CvmDatasetDownloader | None = None,
        downloader_cad: CvmDatasetDownloader | None = None,
        cache: CacheManager | None = None,
        parser_version: str = PARSER_VERSION,
        anos_janela: int = _ANOS_JANELA,
        resolver_code_cvm: Callable[[str], str | None] | None = None,
    ) -> None:
        """Inicializa a fonte com downloaders, cache e resolvedor de codeCVM."""
        self._downloader_fre = downloader_fre or _criar_downloader_fre()
        self._downloader_fca = downloader_fca or _criar_downloader_fca()
        self._downloader_cad = downloader_cad or _criar_downloader_cad()
        self._cache = cache or CacheManager()
        self._parser_version = parser_version
        self._anos_janela = anos_janela
        self._resolver_code_cvm = resolver_code_cvm

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
        """Retorna o CNPJ da companhia resolvido no FCA/cadastro, ou ``None``."""
        try:
            return self._resolver_cnpj(ticker, reference_date)
        except Exception:  # aquisição tolerante por ticker
            logger.warning("Falha ao resolver CNPJ de %s", ticker, exc_info=True)
            return None

    def obter_identidade_papel(
        self: "CvmAcionistasSource", ticker: str, reference_date: date
    ) -> tuple[str | None, str | None]:
        """Retorna ``(CNPJ, razão social)`` do Papel, tolerando indisponibilidade."""
        try:
            chave = ticker.strip().upper()
            cnpj = self._cnpj_fca(chave, reference_date)
            if cnpj is not None:
                return cnpj, self._razao_social(chave, reference_date)
            identidade = self._identidade_cadastro(chave, reference_date)
            if identidade is None:
                return None, None
            return (
                identidade.get("cnpj"),
                identidade.get("razao_social") or None,
            )
        except Exception:  # aquisição tolerante por ticker
            logger.warning(
                "Falha ao resolver identidade de Papel de %s",
                ticker,
                exc_info=True,
            )
            return None, None

    def obter_free_float(
        self: "CvmAcionistasSource", ticker: str, reference_date: date
    ) -> Decimal | None:
        """Retorna o total de ações em circulação (free float), ou ``None``."""
        try:
            cnpj = self._resolver_cnpj(ticker, reference_date)
            if cnpj is None:
                return None
            return self._free_float(cnpj, reference_date)
        except Exception:  # aquisição tolerante por ticker
            logger.warning(
                "Falha ao obter free float de %s", ticker, exc_info=True
            )
            return None

    def _resolver_cnpj(
        self: "CvmAcionistasSource", ticker: str, reference_date: date
    ) -> str | None:
        """Resolve o CNPJ pelo FCA e, sem correspondência, pelo codeCVM."""
        chave = ticker.strip().upper()
        cnpj = self._cnpj_fca(chave, reference_date)
        if cnpj is not None:
            return cnpj
        identidade = self._identidade_cadastro(chave, reference_date)
        return identidade.get("cnpj") if identidade is not None else None

    def _cnpj_fca(
        self: "CvmAcionistasSource", ticker: str, reference_date: date
    ) -> str | None:
        """Resolve o CNPJ pelo casamento exato de ``Codigo_Negociacao`` no FCA."""
        for ano in self._anos(reference_date):
            mapa = self._mapa(
                self._downloader_fca, _ARQUIVO_FCA, "fca", ano, parse_valor_mobiliario
            )
            cnpj = mapa.get(ticker)
            if cnpj is not None:
                return cnpj
        return None

    def _identidade_cadastro(
        self: "CvmAcionistasSource", ticker: str, reference_date: date
    ) -> dict[str, str] | None:
        """Resolve CNPJ e razão social pelo codeCVM no cadastro de companhias."""
        codigo = self._codigo_cvm(ticker)
        if codigo is None:
            return None
        cadastro = self._mapa(
            self._downloader_cad,
            _ARQUIVO_CAD,
            "cad",
            reference_date.year,
            parse_cadastro_cia,
        )
        identidade = cadastro.get(codigo)
        if isinstance(identidade, dict):
            return identidade
        if isinstance(identidade, str):
            return {"cnpj": identidade, "razao_social": ""}
        return None

    def _razao_social(
        self: "CvmAcionistasSource", ticker: str, reference_date: date
    ) -> str | None:
        """Retorna a razão social do cadastro, tolerando falha na consulta."""
        try:
            identidade = self._identidade_cadastro(ticker, reference_date)
        except Exception:  # razão social é complementar ao CNPJ
            logger.warning(
                "Falha ao obter razão social de %s", ticker, exc_info=True
            )
            return None
        if identidade is None:
            return None
        razao = identidade.get("razao_social")
        return razao or None

    def _codigo_cvm(self: "CvmAcionistasSource", ticker: str) -> str | None:
        """Resolve e normaliza o codeCVM do ticker, tolerando indisponibilidade."""
        if self._resolver_code_cvm is None:
            return None
        try:
            codigo = self._resolver_code_cvm(ticker)
        except Exception:  # resolução tolerante
            logger.warning(
                "Falha ao resolver codeCVM de %s", ticker, exc_info=True
            )
            return None
        return _normalizar_codigo_cvm(codigo)

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

    def _free_float(
        self: "CvmAcionistasSource", cnpj: str, reference_date: date
    ) -> Decimal | None:
        """Busca o total de ações em circulação do CNPJ no FRE.

        O mapa normalizado é persistido em JSON (que serializa ``Decimal`` como
        texto); por isso o valor é reconvertido para ``Decimal`` na leitura.
        """
        for ano in self._anos(reference_date):
            mapa = self._mapa(
                self._downloader_fre,
                _ARQUIVO_FRE,
                "fre_float",
                ano,
                parse_acoes_circulacao,
            )
            valor = _decimal(mapa.get(cnpj))
            if valor is not None:
                return valor
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


def _criar_downloader_cad() -> CvmDatasetDownloader:
    """Cria o downloader do cadastro de companhias abertas (CSV direto)."""
    return CvmDatasetDownloader(
        base_url=CAD_BASE_URL,
        arquivo=lambda _ano: _ARQUIVO_CAD,
        dataset="cad",
        parser_version=PARSER_VERSION,
        zipado=False,
    )
