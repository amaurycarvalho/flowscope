"""Constantes de configuração da aquisição de dados de fundos da B3."""

_BASE_URL = "https://sistemaswebb3-listados.b3.com.br/fundsListedProxy/Search"
_LISTED_BASE_URL = (
    "https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall"
)
_NOTICIAS_URL = (
    "https://sistemasweb.b3.com.br/PlantaoNoticias/Noticias/ListarTitulosNoticias"
)
_NOTICIAS_DETALHE_URL = (
    "https://sistemasweb.b3.com.br/PlantaoNoticias/Noticias/Detail"
)
_CENSURAS_URL = (
    "https://www.b3.com.br/pt_br/regulacao/regulacao-de-emissores/censuras-publicas/"
)
_CONDICOES_URL = (
    "https://www.b3.com.br/pt_br/regulacao/regulacao-de-emissores/"
    "condicoes-excepcionais/"
)
_PROGRAMAS_URL = (
    "https://sistemaswebb3-listados.b3.com.br/stockProgramProxy/"
    "StockProgramCall/GetListedCompany"
)
_PROGRAMAS_PAGE_SIZE = 60
_CADASTRO_EMPRESAS_URL = (
    "https://www.b3.com.br/pt_br/produtos-e-servicos/negociacao/consultas/"
    "empresas-listadas/empresas-listadas.csv"
)
_TIPO_PROVENTOS = 41
_PAGE_SIZE = 20
_AGENCIA_PADRAO = "18"

#: URL do documento binário (PDF) no visualizador do FundosNet.
_URL_DOCUMENTO_PDF = "https://fnet.bmfbovespa.com.br/fnet/publico/exibirDocumento"

#: Timeout (segundos) das requisições de documentos no FundosNet.
#:
#: O host do FundosNet eventualmente aceita a conexão mas não responde por
#: dezenas de segundos; com um timeout curto a tentativa falha rápido e o
#: retry estabelece uma nova conexão, em vez de travar a aquisição.
_TIMEOUT_DOCUMENTO = 10

#: Tipos de fundo consultados na resolução de identidade, em ordem de tentativa.
TIPOS_FUNDO = ("FII", "FIAGRO", "FIP", "FIDC")

#: Versão do parser/aquisição usada para versionar as chaves de cache.
PARSER_VERSION = "b3-fii-1"

#: Prazos de validade (em dias) por tipo de dado da aquisição B3.
TTL_FUNDOS_DIAS = 30
TTL_RESOLUCAO_TICKER_DIAS = 30
TTL_CODIGO_CVM_DIAS = 30
TTL_CADASTRO_EMPRESAS_DIAS = 30
TTL_DOCUMENTOS_LISTA_DIAS = 1
TTL_DOCUMENTOS_RELEVANTES_DIAS = 1
TTL_DOCUMENTO_HTML_DIAS = 30
TTL_IDENTIDADE_DIAS = 30
TTL_MATERIAL_FACTS_DIAS = 1
TTL_NOTICIAS_DIAS = 1
TTL_PAGINA_ESTATICA_DIAS = 7

#: Prefixos das chaves de cache da aquisição B3.
_PREFIXO_DOCUMENTO_HTML = "fund_doc_html"
_PREFIXO_IDENTIDADE = "fund_classes"
