"""Domínio da fatia de Notícias do Plantão B3.

Reúne a classificação por tipo, as categorias de topo e as entidades do
catálogo, além das regras puras de reconhecimento do documento vinculado.
"""

from flowscope.domain.noticias.classificacao import (
    TERMOS_EXCEPCIONAIS,
    TIPO_OUTROS,
    TIPOS_NOTICIA,
    classificar_tipo,
    normalizar_texto,
    noticia_excepcional,
)
from flowscope.domain.noticias.entities import (
    CatalogoNoticias,
    NoticiaArquivo,
    SecaoNoticias,
)
from flowscope.domain.noticias.secoes import (
    ESCOPO_NOTICIAS,
    SECAO_CENSURAS,
    SECAO_CONDICOES,
    SECAO_GERAL,
    SECAO_PROGRAMAS,
    SECOES_ORDEM,
    TITULO_NOTICIAS,
)
from flowscope.domain.noticias.vinculo import (
    apontador_pendente,
    extrair_url_vinculada,
    host_suportado,
)

__all__ = [
    "ESCOPO_NOTICIAS",
    "SECAO_CENSURAS",
    "SECAO_CONDICOES",
    "SECAO_GERAL",
    "SECAO_PROGRAMAS",
    "SECOES_ORDEM",
    "TERMOS_EXCEPCIONAIS",
    "TIPOS_NOTICIA",
    "TIPO_OUTROS",
    "TITULO_NOTICIAS",
    "CatalogoNoticias",
    "NoticiaArquivo",
    "SecaoNoticias",
    "apontador_pendente",
    "classificar_tipo",
    "extrair_url_vinculada",
    "host_suportado",
    "normalizar_texto",
    "noticia_excepcional",
]
