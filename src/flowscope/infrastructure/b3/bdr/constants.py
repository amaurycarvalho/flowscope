"""Constantes da aquisição de avisos aos acionistas de BDR."""

#: Base do Plantão de Notícias da B3.
_B3_NOTICIAS_BASE = "https://sistemasweb.b3.com.br/PlantaoNoticias/Noticias"

#: Endpoint de listagem de títulos de notícias do Plantão B3.
NOTICIAS_URL = f"{_B3_NOTICIAS_BASE}/ListarTitulosNoticias"

#: Endpoint da página de detalhe de uma notícia do Plantão B3.
DETAIL_URL = f"{_B3_NOTICIAS_BASE}/Detail"

#: Endpoint do visualizador de arquivos externos da CVM.
CVM_PDF_URL = (
    "https://www.rad.cvm.gov.br/ENETWEB/"
    "frmExibirArquivoIPEExterno.aspx/ExibirPDF"
)

#: Código de instituição usado ao consultar o PDF pelo ``ID`` do documento.
CODIGO_INSTITUICAO = "2"

#: Agência usada na consulta do Plantão de Notícias.
AGENCIA = "18"

#: Janela de meses consultada, mês a mês.
MESES_JANELA = 12

#: TTL do cache de avisos, em dias.
TTL_AVISOS_DIAS = 1

#: Versão do parser/aquisição usada para versionar as chaves de cache.
PARSER_VERSION = "bdr-1"

#: Trecho do título que identifica um aviso aos acionistas.
TERMO_AVISO = "Aviso aos Acionistas"

#: Subpasta do cache de PDFs de BDR sob o diretório de cache.
PASTA_CACHE = "bdr"

#: Versão do parser usada nas chaves de cache dos avisos.
CHAVE_AVISOS = "bdr_avisos"
