"""Regras de aplicação da fatia de Documentos.

Reúne a porta e o read-model do catálogo, as portas de persistência de resumos
e textos, os serviços de resumo/guidance e o seam de persistência do lote.
Depende apenas de ``domain`` — os adaptadores de infraestrutura são injetados
pelo ponto de composição.
"""
