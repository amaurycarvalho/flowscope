"""Cliente HTTP para a API de fundos listados da B3 (fundsListedProxy)."""

import base64
import csv
import io
import json
import logging
from datetime import date, datetime, timedelta, timezone

import requests

from flowscope.domain.structured import (
    Assembleia,
    AvisoAcionista,
    AvisoDebenturista,
    CategoriaMaterialFact,
    DocumentoMaterialFact,
    FatoRelevante,
    NoticiaB3,
)
from flowscope.infrastructure.b3.structured_parser import (
    extrair_censuras,
    extrair_condicoes_excepcionais,
)
from flowscope.infrastructure.cache import CacheManager

logger = logging.getLogger(__name__)

_BASE_URL = "https://sistemaswebb3-listados.b3.com.br/fundsListedProxy/Search"
_LISTED_BASE_URL = (
    "https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall"
)
_NOTICIAS_URL = (
    "https://sistemasweb.b3.com.br/PlantaoNoticias/Noticias/ListarTitulosNoticias"
)
_CENSURAS_URL = (
    "https://www.b3.com.br/pt_br/regulacao/regulacao-de-emissores/censuras-publicas/"
)
_CONDICOES_URL = (
    "https://www.b3.com.br/pt_br/regulacao/regulacao-de-emissores/"
    "condicoes-excepcionais/"
)
_CADASTRO_EMPRESAS_URL = (
    "https://www.b3.com.br/pt_br/produtos-e-servicos/negociacao/consultas/"
    "empresas-listadas/empresas-listadas.csv"
)
_TIPO_PROVENTOS = 41
_PAGE_SIZE = 20
_AGENCIA_PADRAO = "18"


class B3FundosClient:
    """Consulta a API de fundos listados da B3 com cache local.

    Responsável pela resolução de tickers para ``idFNET``, listagem paginada
    de relatórios estruturados e download do HTML dos documentos.
    """

    _BASE_URL = _BASE_URL

    def __init__(self: "B3FundosClient", cache: CacheManager | None = None) -> None:
        """Inicializa o cliente com o gerenciador de cache informado ou um novo padrão."""
        self._cache = cache or CacheManager()

    def _build_token(self: "B3FundosClient", payload: dict[str, object]) -> str:
        """Serializa o payload em JSON compacto e codifica em Base64."""
        raw = json.dumps(payload, separators=(",", ":"))
        return base64.b64encode(raw.encode()).decode()

    def _get_json(self: "B3FundosClient", endpoint: str, payload: dict[str, object]) -> object:
        """Executa o GET do endpoint informado com o token construído do payload."""
        token = self._build_token(payload)
        url = f"{_BASE_URL}/{endpoint}/{token}"
        logger.info("Consultando %s", url)
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def resolver_ticker(
        self: "B3FundosClient",
        ticker: str,
        type_fund: str = "FII",
    ) -> str | None:
        """Resolve o ticker para o ``idFNET`` na B3.

        Retorna ``None`` para tickers sem dados na API de fundos, sem lançar
        exceção. O resultado, inclusive ``None``, é cacheado por 30 dias.
        """
        id_cem = _fund_root(ticker)

        def _fetch() -> dict[str, object]:
            try:
                dados = self._get_json(
                    "GetListClassFund",
                    {
                        "language": "pt-br",
                        "idCEM": id_cem,
                        "typeFund": type_fund,
                    },
                )
            except requests.RequestException as e:
                logger.warning("Falha ao resolver ticker %s: %s", ticker, e)
                return {"idFNET": None}
            if not isinstance(dados, list):
                return {"idFNET": None}
            for item in dados:
                if not isinstance(item, dict):
                    continue
                if "Fundo:" in str(item.get("tradingName", "")):
                    continue
                id_fnet = item.get("id")
                if id_fnet:
                    return {"idFNET": str(id_fnet)}
            return {"idFNET": None}

        key = f"fund_resolution_{ticker.upper()}"
        try:
            payload = self._cache.get_or_fetch(key, ttl_days=30, fetch_fn=_fetch)
        except requests.RequestException:
            logger.warning("Falha ao resolver ticker %s", ticker, exc_info=True)
            return None
        return payload.get("idFNET")

    def listar_documentos(
        self: "B3FundosClient",
        id_fnet: str,
        data_inicio: date,
        data_fim: date,
        tipo: int = _TIPO_PROVENTOS,
        type_fund: str = "FII",
    ) -> list[dict]:
        """Lista os relatórios estruturados do tipo informado, paginando quando necessário."""
        documentos: list[dict] = []
        page_number = 1
        while True:
            pagina = self._listar_pagina(
                id_fnet, data_inicio, data_fim, tipo, type_fund, page_number
            )
            resultados = pagina.get("results", [])
            if isinstance(resultados, list):
                documentos.extend(resultados)
            total_pages = int(pagina.get("page", {}).get("totalPages", 1) or 1)
            if page_number >= total_pages:
                break
            page_number += 1
        return documentos

    def _listar_pagina(
        self: "B3FundosClient",
        id_fnet: str,
        data_inicio: date,
        data_fim: date,
        tipo: int,
        type_fund: str,
        page_number: int,
    ) -> dict[str, object]:
        """Busca uma página da listagem de relatórios, com cache de 1 dia."""
        key = (
            f"fund_docs_{id_fnet}_{tipo}_{data_inicio.isoformat()}_"
            f"{data_fim.isoformat()}_{page_number}"
        )

        def _fetch() -> dict[str, object]:
            return self._get_json(
                "GetStructuredReports",
                {
                    "language": "pt-br",
                    "dataInicial": data_inicio.isoformat(),
                    "dataFinal": data_fim.isoformat(),
                    "pageNumber": page_number,
                    "pageSize": _PAGE_SIZE,
                    "idFNET": id_fnet,
                    "typeFund": type_fund,
                    "type": tipo,
                },
            )

        try:
            return self._cache.get_or_fetch(key, ttl_days=1, fetch_fn=_fetch)
        except requests.RequestException:
            logger.warning(
                "Falha ao listar documentos do idFNET %s (página %d)",
                id_fnet,
                page_number,
                exc_info=True,
            )
            return {"results": [], "page": {"totalPages": 1, "totalRecords": 0}}

    def buscar_html_documento(self: "B3FundosClient", id_documento: str) -> str:
        """Baixa e retorna o HTML do documento de provento informado."""
        url = (
            "https://fnet.bmfbovespa.com.br/fnet/publico/exibirDocumento"
            f"?id={id_documento}"
        )
        logger.info("Baixando documento %s via %s", id_documento, url)
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        return resp.text

    def _get_listed_json(
        self: "B3FundosClient",
        endpoint: str,
        payload: dict[str, object],
    ) -> object:
        """Executa o GET do proxy de empresas listadas com token Base64."""
        token = self._build_token(payload)
        url = f"{_LISTED_BASE_URL}/{endpoint}/{token}"
        logger.info("Consultando %s", url)
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def resolver_code_cvm(self: "B3FundosClient", ticker: str) -> str | None:
        """Resolve o ticker para o ``codeCVM`` na B3.

        Consulta a API ``listedCompaniesProxy`` e, quando indisponível, baixa o
        cadastro de empresas listadas como alternativa. Retorna ``None`` para
        tickers sem código CVM, sem lançar exceção. O resultado, inclusive
        ``None``, é cacheado por 30 dias.
        """
        key = f"codecvm_{ticker.strip().upper()}"

        def _fetch() -> dict[str, object]:
            try:
                return {"codeCVM": self._consultar_code_cvm_por_api(ticker)}
            except requests.RequestException as e:
                logger.warning(
                    "API de empresas indisponível para %s, usando cadastro: %s",
                    ticker,
                    e,
                )
                return {"codeCVM": self._consultar_code_cvm_no_cadastro(ticker)}

        try:
            payload = self._cache.get_or_fetch(key, ttl_days=30, fetch_fn=_fetch)
        except requests.RequestException:
            logger.warning(
                "Falha ao resolver codeCVM do ticker %s", ticker, exc_info=True
            )
            return None
        return payload.get("codeCVM")

    def _consultar_code_cvm_por_api(
        self: "B3FundosClient", ticker: str
    ) -> str | None:
        """Consulta a API de empresas listadas por ticker."""
        dados = self._get_listed_json(
            "GetListedCompany",
            {
                "language": "pt-br",
                "pageNumber": 1,
                "pageSize": 20,
                "tradingName": ticker.strip().upper(),
            },
        )
        resultados = dados.get("results", []) if isinstance(dados, dict) else []
        for item in resultados:
            if not isinstance(item, dict):
                continue
            codigo = item.get("codeCVM")
            if codigo:
                return _normalizar_code_cvm(str(codigo))
        return None

    def _consultar_code_cvm_no_cadastro(
        self: "B3FundosClient", ticker: str
    ) -> str | None:
        """Busca o codeCVM no cadastro de empresas listadas da B3."""
        indice = self._carregar_indice_code_cvm()
        return indice.get(ticker.strip().upper())

    def _carregar_indice_code_cvm(self: "B3FundosClient") -> dict[str, str]:
        """Baixa e cacheia o índice ticker→codeCVM do cadastro de empresas."""
        key = "cadastro_empresas_code_cvm"

        def _fetch() -> dict[str, object]:
            texto = self._baixar_cadastro_empresas()
            return {"indice": montar_indice_code_cvm(texto)}

        payload = self._cache.get_or_fetch(key, ttl_days=30, fetch_fn=_fetch)
        indice = payload.get("indice")
        return indice if isinstance(indice, dict) else {}

    def _baixar_cadastro_empresas(self: "B3FundosClient") -> str:
        """Baixa o CSV do cadastro de empresas listadas da B3."""
        logger.info("Baixando cadastro de empresas via %s", _CADASTRO_EMPRESAS_URL)
        resp = requests.get(_CADASTRO_EMPRESAS_URL, timeout=60)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        return resp.text

    def listar_fatos_relevantes(
        self: "B3FundosClient",
        code_cvm: str,
        categoria: CategoriaMaterialFact | str,
        data_inicio: date,
        data_fim: date,
        ticker: str = "",
    ) -> list[DocumentoMaterialFact]:
        """Lista documentos do ``GetMaterialFacts`` paginando todas as páginas.

        A categoria é validada antes de qualquer requisição HTTP. O resultado
        é cacheado por 1 dia usando a chave composta por ``codeCVM``,
        ``categoria`` e período.
        """
        codigo_categoria = _codigo_categoria(categoria)
        key = (
            f"matfacts_{code_cvm}_{codigo_categoria}_"
            f"{data_inicio.isoformat()}_{data_fim.isoformat()}"
        )

        def _fetch() -> dict[str, object]:
            itens = self._coletar_paginas_material_facts(
                code_cvm, codigo_categoria, data_inicio, data_fim
            )
            return {"results": itens}

        try:
            payload = self._cache.get_or_fetch(key, ttl_days=1, fetch_fn=_fetch)
        except requests.RequestException:
            logger.warning(
                "Falha ao listar fatos relevantes do codeCVM %s", code_cvm,
                exc_info=True,
            )
            return []
        resultados = payload.get("results") or []
        return [
            _converter_item_material_fact(item, ticker=ticker, code_cvm=code_cvm)
            for item in resultados
            if isinstance(item, dict)
        ]

    def _coletar_paginas_material_facts(
        self: "B3FundosClient",
        code_cvm: str,
        codigo_categoria: str,
        data_inicio: date,
        data_fim: date,
    ) -> list[dict]:
        """Coleta os itens brutos de todas as páginas do ``GetMaterialFacts``."""
        resultados: list[dict] = []
        page_number = 1
        while True:
            dados = self._get_listed_json(
                "GetMaterialFacts",
                {
                    "linguagem": "pt-br",
                    "codeCVM": code_cvm,
                    "year": data_inicio.year,
                    "dataInicial": data_inicio.isoformat(),
                    "dataFinal": data_fim.isoformat(),
                    "categoria": codigo_categoria,
                    "pageNumber": page_number,
                    "pageSize": _PAGE_SIZE,
                },
            )
            pagina = dados.get("page", {}) if isinstance(dados, dict) else {}
            itens = dados.get("results") if isinstance(dados, dict) else []
            if isinstance(itens, list):
                resultados.extend(item for item in itens if isinstance(item, dict))
            total_pages = int(pagina.get("totalPages", 1) or 1) if pagina else 1
            if page_number >= total_pages:
                break
            page_number += 1
        return resultados

    def listar_noticias(
        self: "B3FundosClient",
        agencia: str = _AGENCIA_PADRAO,
        data_inicio: date | None = None,
        data_fim: date | None = None,
        palavra: str | None = None,
    ) -> list[NoticiaB3]:
        """Lista notícias do Plantão B3 no período e com filtro informados.

        Sem período informado, consulta os últimos 30 dias. O resultado é
        cacheado por cerca de 1 hora, usando o horário na chave de cache.
        """
        hoje = datetime.now(timezone.utc).date()
        data_inicial = data_inicio or hoje - timedelta(days=30)
        data_final = data_fim or hoje
        palavra_filtro = palavra or ""
        hora = datetime.now(timezone.utc).strftime("%Y%m%d%H")
        key = (
            f"noticias_{agencia}_{data_inicial.isoformat()}_"
            f"{data_final.isoformat()}_{palavra_filtro}_{hora}"
        )

        def _fetch() -> dict[str, object]:
            itens = self._coletar_noticias(
                agencia, data_inicial, data_final, palavra_filtro
            )
            return {"noticias": itens}

        try:
            payload = self._cache.get_or_fetch(key, ttl_days=1, fetch_fn=_fetch)
        except requests.RequestException:
            logger.warning("Falha ao listar notícias da B3", exc_info=True)
            return []
        itens = payload.get("noticias") or []
        return [
            _converter_item_noticia(item, agencia=agencia)
            for item in itens
            if isinstance(item, dict)
        ]

    def _coletar_noticias(
        self: "B3FundosClient",
        agencia: str,
        data_inicial: date,
        data_final: date,
        palavra: str,
    ) -> list[dict]:
        """Coleta as notícias brutas, paginando quando a API informar páginas."""
        parametros: dict[str, object] = {
            "agencia": agencia,
            "palavra": palavra,
            "dataInicial": data_inicial.isoformat(),
            "dataFinal": data_final.isoformat(),
        }

        def _buscar() -> object:
            logger.info("Consultando %s", _NOTICIAS_URL)
            resp = requests.get(_NOTICIAS_URL, params=parametros, timeout=30)
            resp.raise_for_status()
            return resp.json()

        dados = _buscar()
        itens = _itens_de_noticias(dados)
        pagina = dados.get("page", {}) if isinstance(dados, dict) else {}
        total_pages = int(pagina.get("totalPages", 1) or 1) if pagina else 1
        for page_number in range(2, total_pages + 1):
            parametros["pageNumber"] = page_number
            itens.extend(_itens_de_noticias(_buscar()))
        return itens

    def listar_censuras(self: "B3FundosClient") -> list:
        """Lista as censuras públicas da página da B3, com cache de 7 dias."""
        html = self._html_cacheado(
            "censuras_publicas", _CENSURAS_URL, "página de censuras públicas"
        )
        return extrair_censuras(html)

    def listar_condicoes_excepcionais(self: "B3FundosClient") -> list:
        """Lista as condições excepcionais da página da B3, com cache de 7 dias."""
        html = self._html_cacheado(
            "condicoes_excepcionais",
            _CONDICOES_URL,
            "página de condições excepcionais",
        )
        return extrair_condicoes_excepcionais(html)

    def _html_cacheado(
        self: "B3FundosClient", key: str, url: str, descricao: str
    ) -> str:
        """Baixa e cacheia o HTML de uma página estática da B3 por 7 dias."""
        def _fetch() -> dict[str, object]:
            logger.info("Baixando %s", url)
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or "utf-8"
            return {"html": resp.text}

        try:
            payload = self._cache.get_or_fetch(key, ttl_days=7, fetch_fn=_fetch)
        except requests.RequestException as e:
            raise RuntimeError(f"Não foi possível acessar a {descricao}: {e}") from e
        return str(payload.get("html") or "")


def _fund_root(ticker: str) -> str:
    """Remove o sufixo ``11`` do ticker, devolvendo o código do fundo."""
    ticker = ticker.strip().upper()
    if ticker.endswith("11"):
        return ticker[:-2]
    return ticker


def _codigo_categoria(categoria: CategoriaMaterialFact | str) -> str:
    """Valida e retorna o código numérico de uma categoria do material fact."""
    if isinstance(categoria, CategoriaMaterialFact):
        return categoria.value
    codigo = str(categoria)
    try:
        return CategoriaMaterialFact(codigo).value
    except ValueError:
        raise ValueError(f"Categoria GetMaterialFacts inválida: {categoria!r}") from None


def _normalizar_code_cvm(valor: str) -> str:
    """Remove os zeros à esquerda de um código CVM."""
    valor = valor.strip()
    normalizado = valor.lstrip("0")
    return normalizado or "0"


def _string_ou_none(valor: object) -> str | None:
    """Retorna a string do valor, ou ``None`` quando vazio."""
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto if texto else None


def _normalizar_rotulo(rotulo: str) -> str:
    """Normaliza um rótulo para comparação, sem acentos e espaços."""
    trocas = {
        "ç": "c",
        "á": "a",
        "ã": "a",
        "à": "a",
        "â": "a",
        "é": "e",
        "ê": "e",
        "í": "i",
        "ó": "o",
        "ô": "o",
        "õ": "o",
        "ú": "u",
    }
    texto = rotulo.strip().lower()
    for origem, destino in trocas.items():
        texto = texto.replace(origem, destino)
    return "".join(texto.split())


_ROTULOS_CLASSES: dict[str, type] = {
    "assembleia": Assembleia,
    "assembleias": Assembleia,
    "fatorelevante": FatoRelevante,
    "fatosrelevantes": FatoRelevante,
    "avisoacionista": AvisoAcionista,
    "avisoacionistas": AvisoAcionista,
    "avisoaosacionistas": AvisoAcionista,
    "avisodebenturista": AvisoDebenturista,
    "avisodebenturistas": AvisoDebenturista,
    "avisoaosdebenturistas": AvisoDebenturista,
}


def _classe_material_fact(categoria: str) -> type:
    """Retorna a classe de entidade correspondente à categoria da API."""
    if not categoria:
        return DocumentoMaterialFact
    return _ROTULOS_CLASSES.get(_normalizar_rotulo(categoria), DocumentoMaterialFact)


def _converter_item_material_fact(
    item: dict, *, ticker: str, code_cvm: str
) -> DocumentoMaterialFact:
    """Monta a entidade de domínio a partir de um item bruto do ``GetMaterialFacts``."""
    company = item.get("company")
    empresa = ""
    if isinstance(company, dict):
        empresa = _string_ou_none(company.get("companyName")) or ""
    categoria = _string_ou_none(item.get("category")) or ""
    campos = {
        "code_cvm": code_cvm,
        "empresa": empresa,
        "ticker": ticker,
        "data_referencia": _string_ou_none(item.get("dateReference")) or "",
        "data_entrega": _string_ou_none(item.get("deliveryDate")),
        "categoria": categoria,
        "tipo": _string_ou_none(item.get("type")),
        "especie": _string_ou_none(item.get("kind")),
        "status": _string_ou_none(item.get("status")),
        "assunto": _string_ou_none(item.get("subject")) or "",
        "url_documento": _string_ou_none(item.get("urlSearch")),
        "url_download": _string_ou_none(item.get("urlDownload")),
    }
    classe = _classe_material_fact(categoria)
    if classe is Assembleia:
        return Assembleia(
            **campos,
            tipo_assembleia=campos["tipo"],
            especie_documento=campos["especie"],
        )
    return classe(**campos)


def _itens_de_noticias(dados: object) -> list[dict]:
    """Extrai os itens de notícia da resposta da API do Plantão B3."""
    if isinstance(dados, list):
        return [item for item in dados if isinstance(item, dict)]
    if not isinstance(dados, dict):
        return []
    return [
        item for item in (dados.get("results") or []) if isinstance(item, dict)
    ]


def _converter_item_noticia(item: dict, *, agencia: str) -> NoticiaB3:
    """Monta a entidade ``NoticiaB3`` a partir de um item bruto do Plantão B3."""
    titulo = (
        _string_ou_none(item.get("titulo"))
        or _string_ou_none(item.get("title"))
        or ""
    )
    data_publicacao = (
        _string_ou_none(item.get("dataPublicacao"))
        or _string_ou_none(item.get("dataNoticia"))
        or _string_ou_none(item.get("data"))
        or ""
    )
    url = _string_ou_none(item.get("url")) or _string_ou_none(item.get("link"))
    return NoticiaB3(
        titulo=titulo,
        data_publicacao=data_publicacao,
        url=url,
        agencia=str(agencia),
    )


def montar_indice_code_cvm(texto_csv: str) -> dict[str, str]:
    """Constrói o índice ticker→codeCVM a partir do CSV do cadastro da B3."""
    if not texto_csv:
        return {}
    dialeto = csv.Sniffer().sniff(texto_csv[:4096], delimiters=";,|")
    leitor = csv.DictReader(io.StringIO(texto_csv), delimiter=dialeto.delimiter)
    coluna_cvm = _coluna_com(leitor.fieldnames, ["cvm"])
    coluna_ticker = _coluna_com(
        leitor.fieldnames,
        ["ticker", "codnegociacao", "codigodenegociacao", "acao", "codigo"],
    )
    if coluna_cvm is None or coluna_ticker is None:
        return {}
    indice: dict[str, str] = {}
    for linha in leitor:
        ticker = str(linha.get(coluna_ticker) or "").strip().upper()
        codigo = str(linha.get(coluna_cvm) or "").strip()
        if not ticker or not codigo.isdigit():
            continue
        indice[ticker] = _normalizar_code_cvm(codigo)
    return indice


def _coluna_com(colunas: list[str] | None, termos: list[str]) -> str | None:
    """Retorna a primeira coluna cujo nome contém um dos termos informados."""
    if not colunas:
        return None
    normalizadas = {_normalizar_rotulo(coluna): coluna for coluna in colunas}
    for coluna_normalizada, coluna in normalizadas.items():
        if any(termo in coluna_normalizada for termo in termos):
            return coluna
    return None
