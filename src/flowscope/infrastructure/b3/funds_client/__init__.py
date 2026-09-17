"""Cliente HTTP para a API de fundos listados da B3 (fundsListedProxy).

Este pacote mantém o caminho de importação histórico
``flowscope.infrastructure.b3.funds_client`` e organiza o cliente em mixins
por responsabilidade:

- ``base``: primitivas HTTP, sessão e retry.
- ``fundos``: listagem de fundos e resolução de ticker.
- ``documentos``: relatórios estruturados e HTML de documentos.
- ``code_cvm``: resolução de ticker→codeCVM.
- ``material_facts``: fatos relevantes e avisos.
- ``noticias``: notícias do Plantão B3.
- ``regulatorio``: censuras públicas e condições excepcionais.
"""

from flowscope.infrastructure.b3.funds_client.base import _FundosBase
from flowscope.infrastructure.b3.funds_client.code_cvm import FundosCodeCvmMixin
from flowscope.infrastructure.b3.funds_client.constants import (
    _AGENCIA_PADRAO,
    _BASE_URL,
    _CADASTRO_EMPRESAS_URL,
    _CENSURAS_URL,
    _CONDICOES_URL,
    _LISTED_BASE_URL,
    _NOTICIAS_URL,
    _PAGE_SIZE,
    _PREFIXO_DOCUMENTO_HTML,
    _PREFIXO_IDENTIDADE,
    _TIPO_PROVENTOS,
    PARSER_VERSION,
    TIPOS_FUNDO,
    TTL_CADASTRO_EMPRESAS_DIAS,
    TTL_CODIGO_CVM_DIAS,
    TTL_DOCUMENTO_HTML_DIAS,
    TTL_DOCUMENTOS_LISTA_DIAS,
    TTL_FUNDOS_DIAS,
    TTL_IDENTIDADE_DIAS,
    TTL_MATERIAL_FACTS_DIAS,
    TTL_NOTICIAS_DIAS,
    TTL_PAGINA_ESTATICA_DIAS,
    TTL_RESOLUCAO_TICKER_DIAS,
)
from flowscope.infrastructure.b3.funds_client.cvm import (
    _coluna_com,
    _normalizar_code_cvm,
    montar_indice_code_cvm,
)
from flowscope.infrastructure.b3.funds_client.documentos import FundosDocumentosMixin
from flowscope.infrastructure.b3.funds_client.fundos import FundosListagemMixin
from flowscope.infrastructure.b3.funds_client.fundos_helpers import (
    _fund_root,
    _selecionar_fund,
)
from flowscope.infrastructure.b3.funds_client.material_facts import (
    FundosMaterialFactsMixin,
)
from flowscope.infrastructure.b3.funds_client.material_facts_convert import (
    _ROTULOS_CLASSES,
    _classe_material_fact,
    _codigo_categoria,
    _converter_item_material_fact,
)
from flowscope.infrastructure.b3.funds_client.noticias import FundosNoticiasMixin
from flowscope.infrastructure.b3.funds_client.noticias_convert import (
    _converter_item_noticia,
    _itens_de_noticias,
)
from flowscope.infrastructure.b3.funds_client.regulatorio import FundosRegulatorioMixin
from flowscope.infrastructure.b3.funds_client.texto import (
    _normalizar_rotulo,
    _string_ou_none,
)


def _chave_cache(prefixo: str, *partes: object) -> str:
    """Monta uma chave de cache versionada pela versão do parser/aquisição."""
    sufixo = "_".join(str(parte) for parte in partes)
    return f"{prefixo}_{PARSER_VERSION}_{sufixo}" if sufixo else f"{prefixo}_{PARSER_VERSION}"


class B3FundosClient(
    _FundosBase,
    FundosListagemMixin,
    FundosDocumentosMixin,
    FundosCodeCvmMixin,
    FundosMaterialFactsMixin,
    FundosNoticiasMixin,
    FundosRegulatorioMixin,
):
    """Consulta a API de fundos listados da B3 com cache local.

    Responsável pela resolução de tickers para ``idFNET``, listagem paginada
    de relatórios estruturados e download do HTML dos documentos.
    """

    def _chave_cache(self: "B3FundosClient", prefixo: str, *partes: object) -> str:
        """Delega para a função de módulo, respeitando a versão vigente."""
        return _chave_cache(prefixo, *partes)


__all__ = [
    "PARSER_VERSION",
    "TIPOS_FUNDO",
    "TTL_CADASTRO_EMPRESAS_DIAS",
    "TTL_CODIGO_CVM_DIAS",
    "TTL_DOCUMENTOS_LISTA_DIAS",
    "TTL_DOCUMENTO_HTML_DIAS",
    "TTL_FUNDOS_DIAS",
    "TTL_IDENTIDADE_DIAS",
    "TTL_MATERIAL_FACTS_DIAS",
    "TTL_NOTICIAS_DIAS",
    "TTL_PAGINA_ESTATICA_DIAS",
    "TTL_RESOLUCAO_TICKER_DIAS",
    "_AGENCIA_PADRAO",
    "_BASE_URL",
    "_CADASTRO_EMPRESAS_URL",
    "_CENSURAS_URL",
    "_CONDICOES_URL",
    "_LISTED_BASE_URL",
    "_NOTICIAS_URL",
    "_PAGE_SIZE",
    "_PREFIXO_DOCUMENTO_HTML",
    "_PREFIXO_IDENTIDADE",
    "_ROTULOS_CLASSES",
    "_TIPO_PROVENTOS",
    "B3FundosClient",
    "_chave_cache",
    "_classe_material_fact",
    "_codigo_categoria",
    "_coluna_com",
    "_converter_item_material_fact",
    "_converter_item_noticia",
    "_fund_root",
    "_itens_de_noticias",
    "_normalizar_code_cvm",
    "_normalizar_rotulo",
    "_selecionar_fund",
    "_string_ou_none",
    "montar_indice_code_cvm",
]
