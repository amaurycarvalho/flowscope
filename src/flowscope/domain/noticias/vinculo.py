"""Regras puras de reconhecimento e pendência do documento vinculado.

Algumas notícias "Geral" não trazem o conteúdo no corpo: o ``#conteudoDetalhe``
é apenas um apontador em texto puro para um documento. Estas funções reconhecem
as URLs suportadas (visualizador da CVM RAD e do FNET) e decidem se o texto
cacheado ainda é o apontador não resolvido. O download em si é infraestrutura.
"""

import re

#: Regex de uma URL absoluta no corpo da notícia.
_URL = re.compile(r"https?://[^\s<>\"']+")

#: Trechos que identificam o visualizador de documentos da CVM (RAD).
_HOST_CVM_RAD = "rad.cvm.gov.br"
_PAGINA_CVM_RAD = "frmExibirArquivoIPEExterno.aspx"

#: Trechos que identificam o visualizador de documentos do FNET.
_HOST_FNET = "fnet.bmfbovespa.com.br"
_PAGINA_FNET = "visualizarDocumento"


def extrair_url_vinculada(texto: str) -> str | None:
    """Retorna a primeira URL suportada (CVM RAD ou FNET) embutida no corpo."""
    if not texto:
        return None
    for bruta in _URL.findall(texto):
        url = bruta.rstrip(".,;)")
        if host_suportado(url) is not None:
            return url
    return None


def host_suportado(url: str) -> str | None:
    """Identifica o resolvedor aplicável à URL, ou ``None``."""
    if _HOST_CVM_RAD in url and _PAGINA_CVM_RAD in url:
        return "cvm"
    if _HOST_FNET in url and _PAGINA_FNET in url:
        return "fnet"
    return None


def apontador_pendente(texto: str, corpo: str) -> bool:
    """Indica se ``texto`` ainda é o apontador não resolvido do ``corpo``.

    Vale quando o texto contém uma URL suportada e é idêntico ao corpo atual do
    ``#conteudoDetalhe`` (ou seja, o download do documento vinculado não
    concluiu). A comparação evita tratar como pendente um documento já resolvido
    que porventura cite uma URL suportada.
    """
    return bool(corpo) and texto == corpo and extrair_url_vinculada(texto) is not None
