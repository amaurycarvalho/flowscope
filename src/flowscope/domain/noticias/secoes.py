"""Categorias de topo da sub-aba "Notícias" e sua ordem de exibição."""

#: Título-raiz da árvore da sub-aba "Notícias".
TITULO_NOTICIAS = "Notícias"

#: Escopo usado como "ticker" nos stores de texto e resumo (notícias são globais).
ESCOPO_NOTICIAS = "NOTICIAS"

#: Categoria de topo "Geral" (notícias do Plantão B3).
SECAO_GERAL = "Geral"

#: Categoria de topo das censuras públicas.
SECAO_CENSURAS = "Censuras Públicas"

#: Categoria de topo das condições excepcionais.
SECAO_CONDICOES = "Condições Excepcionais"

#: Categoria de topo dos programas de aquisição de ações.
SECAO_PROGRAMAS = "Programas de Aquisição de Ações"

#: Ordem de exibição e de processamento das categorias de topo. A "Geral" fica
#: por último para que sua carga (pesada, um download por artigo) e seus
#: resumos só ocorram depois das fontes regulatórias.
SECOES_ORDEM = (SECAO_CENSURAS, SECAO_CONDICOES, SECAO_PROGRAMAS, SECAO_GERAL)
