"""Estratégias flexíveis de parsing de HTML tabular de documentos da B3.

Este pacote mantém o caminho de importação histórico
``flowscope.infrastructure.b3.structured_parser`` e reexporta as funções de
parsing agora organizadas por responsabilidade:

- ``html_utils``: navegação e normalização de HTML.
- ``rotulos``: extração de valores por rótulo.
- ``tabelas``: extração de tabelas e identificação de contexto/tipo.
- ``valores``: conversão de valores monetários, datas e isenções.
- ``censuras``: extração de censuras públicas.
- ``condicoes``: extração de condições excepcionais.
"""

from flowscope.infrastructure.b3.structured_parser.censuras import (
    _DATA_CENSURA_RE,
    _TICKER_RE,
    _conteudo_do_bloco,
    _data_do_bloco,
    _data_em_texto,
    _extrair_censura_do_bloco,
    _titulo_e_ticker_do_bloco,
    extrair_censuras,
)
from flowscope.infrastructure.b3.structured_parser.condicoes import (
    extrair_condicoes_excepcionais,
)
from flowscope.infrastructure.b3.structured_parser.html_utils import (
    _celulas_da_linha,
    _normalizar,
    _texto_apos_no_parent,
    _texto_apos_rotulo,
    _texto_do_irmao_seguinte,
    _texto_do_proximo_sibling,
    _valor_ou_none,
    parse_html,
)
from flowscope.infrastructure.b3.structured_parser.rotulos import (
    _pares_rotulo_valor,
    _rotulo_em_celula,
    extrair_por_rotulo,
)
from flowscope.infrastructure.b3.structured_parser.tabelas import (
    _celula_em,
    _celula_numerica,
    _chave_rotulo_provento,
    _eh_tabela_rotulo_valor,
    _extrair_dados_tabela,
    _extrair_provento_duas_colunas,
    _extrair_tabela_sem_cabecalho,
    _grade_da_linha,
    _indices_colunas_provento,
    _linhas_como_dict,
    _linhas_dados_provento,
    _localizar_cabecalho_provento,
    _montar_provento_duas_colunas,
    _tipo_marcado,
    _tipo_rendimento,
    extrair_tabelas,
    identificar_contexto_tabela,
    identificar_tipo_provento,
)
from flowscope.infrastructure.b3.structured_parser.valores import (
    converter_data_br_para_iso,
    extrair_isento_ir,
    extrair_nota_isencao,
    extrair_por_regex,
    limpar_valor_monetario,
)

__all__ = [
    "_DATA_CENSURA_RE",
    "_TICKER_RE",
    "_celula_em",
    "_celula_numerica",
    "_celulas_da_linha",
    "_chave_rotulo_provento",
    "_conteudo_do_bloco",
    "_data_do_bloco",
    "_data_em_texto",
    "_eh_tabela_rotulo_valor",
    "_extrair_censura_do_bloco",
    "_extrair_dados_tabela",
    "_extrair_provento_duas_colunas",
    "_extrair_tabela_sem_cabecalho",
    "_grade_da_linha",
    "_indices_colunas_provento",
    "_linhas_como_dict",
    "_linhas_dados_provento",
    "_localizar_cabecalho_provento",
    "_montar_provento_duas_colunas",
    "_normalizar",
    "_pares_rotulo_valor",
    "_rotulo_em_celula",
    "_texto_apos_no_parent",
    "_texto_apos_rotulo",
    "_texto_do_irmao_seguinte",
    "_texto_do_proximo_sibling",
    "_tipo_marcado",
    "_tipo_rendimento",
    "_titulo_e_ticker_do_bloco",
    "_valor_ou_none",
    "converter_data_br_para_iso",
    "extrair_censuras",
    "extrair_condicoes_excepcionais",
    "extrair_isento_ir",
    "extrair_nota_isencao",
    "extrair_por_regex",
    "extrair_por_rotulo",
    "extrair_tabelas",
    "identificar_contexto_tabela",
    "identificar_tipo_provento",
    "limpar_valor_monetario",
    "parse_html",
]
