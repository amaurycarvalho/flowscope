"""Regras de aplicação da fatia de Notícias.

Reúne a porta e o read-model do catálogo, a ordenação do lote de resumos e a
montagem do índice compacto consumido pelo contexto do chat. Depende apenas de
``domain`` e da aplicação de Documentos; os adaptadores de infraestrutura são
injetados pelo ponto de composição.
"""
