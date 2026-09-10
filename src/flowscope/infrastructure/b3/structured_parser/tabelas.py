"""Extração de tabelas HTML e identificação de contexto/tipo de provento."""

from bs4 import BeautifulSoup, Tag

from flowscope.infrastructure.b3.structured_parser.html_utils import (
    _celulas_da_linha,
    _normalizar,
)
from flowscope.infrastructure.b3.structured_parser.rotulos import (
    _pares_rotulo_valor,
    _rotulo_em_celula,
)


def extrair_tabelas(soup: BeautifulSoup) -> list[dict]:
    """Extrai todas as tabelas HTML como dicionários com contexto e dados.

    O campo ``dados`` contém uma lista de dicionários. Em tabelas de
    rótulo/valor (formato predominante nos documentos da B3), cada tabela
    produz um único dicionário com os pares rótulo→valor extraídos.
    """
    tabelas: list[dict] = []
    for table in soup.find_all("table"):
        contexto = identificar_contexto_tabela(table)
        dados = _extrair_dados_tabela(table)
        tabelas.append({"contexto": contexto, "dados": dados})
    return tabelas


def _extrair_dados_tabela(table: Tag) -> list[dict]:
    """Extrai os dados de uma tabela, tratando os formatos tabulares da B3.

    - Tabelas com ``<thead>``: cada linha vira um dicionário com os cabeçalhos.
    - Tabelas de rótulo/valor: um único dicionário com os pares rótulo→valor.
    - Demais tabelas: a primeira linha é usada como cabeçalho quando parece
      conter rótulos de coluna.
    """
    thead = table.find("thead")
    header_row: list[str] = []
    if thead is not None:
        header_row = [
            th.get_text(" ", strip=True)
            for th in thead.find_all("th")
            if th.get_text(" ", strip=True)
        ]

    tbody = table.find("tbody") or table
    linhas = tbody.find_all("tr")
    if not linhas:
        return []

    if header_row:
        return _linhas_como_dict(linhas, header_row)

    return _extrair_tabela_sem_cabecalho(linhas)


def _extrair_tabela_sem_cabecalho(linhas: list[Tag]) -> list[dict]:
    """Extrai uma tabela sem ``<thead>``, do provento ou de rótulo/valor."""
    provento_duas_colunas = _extrair_provento_duas_colunas(linhas)
    if provento_duas_colunas is not None:
        return [provento_duas_colunas]

    if _eh_tabela_rotulo_valor(linhas):
        agrupado: dict[str, str] = {}
        for row in linhas:
            cells = _celulas_da_linha(row)
            agrupado.update(_pares_rotulo_valor(cells))
        return [agrupado] if agrupado else []

    return _linhas_como_dict(linhas, [])


def _linhas_como_dict(linhas: list[Tag], headers: list[str]) -> list[dict]:
    """Monta dicionários por linha usando os cabeçalhos informados."""
    rows: list[dict] = []
    for row in linhas:
        cells = _celulas_da_linha(row)
        if not cells:
            continue
        if not headers:
            headers = cells
            continue
        row_data: dict[str, str] = {}
        for idx, cell in enumerate(cells):
            if idx < len(headers) and headers[idx]:
                row_data[headers[idx]] = cell
        if row_data:
            rows.append(row_data)
    return rows


def _eh_tabela_rotulo_valor(linhas: list[Tag]) -> bool:
    """Indica se as linhas representam pares de rótulo/valor.

    Uma tabela de rótulo/valor tem, em quase todas as linhas, uma primeira
    célula rotulando o conteúdo das células seguintes.
    """
    rotuladas = 0
    total = 0
    for row in linhas:
        cells = _celulas_da_linha(row)
        if len(cells) < 2:
            continue
        total += 1
        if _rotulo_em_celula(cells[0]):
            rotuladas += 1
    if total == 0:
        return False
    return rotuladas / total >= 0.5


def _grade_da_linha(linha: Tag) -> list[str]:
    """Retorna as células da linha expandindo ``colspan`` para alinhar colunas."""
    celulas: list[str] = []
    for celula in linha.find_all(["td", "th"]):
        texto = celula.get_text(" ", strip=True)
        try:
            colspan = int(celula.get("colspan") or 1)
        except (TypeError, ValueError):
            colspan = 1
        celulas.append(texto)
        celulas.extend([""] * max(colspan - 1, 0))
    return celulas


def _indices_colunas_provento(
    celulas: list[str],
) -> tuple[int | None, int | None]:
    """Retorna os índices das colunas ``Rendimento`` e ``Amortização``."""
    rendimento: int | None = None
    amortizacao: int | None = None
    for indice, celula in enumerate(celulas):
        normalizado = _normalizar(celula)
        if normalizado == "rendimento" and rendimento is None:
            rendimento = indice
        elif normalizado == "amortizacao" and amortizacao is None:
            amortizacao = indice
    return rendimento, amortizacao


def _chave_rotulo_provento(rotulo: str) -> str | None:
    """Mapeia o rótulo de uma linha do provento para a chave canônica."""
    normalizado = _normalizar(rotulo).split("(", 1)[0]
    normalizado = normalizado.replace("-", "").replace("/", "")
    if normalizado.startswith("database"):
        return "Data-base"
    if normalizado.startswith("valordoprovento"):
        return "Valor do provento (R$/unidade)"
    if normalizado.startswith("datadopagamento"):
        return "Data do pagamento"
    if normalizado.startswith("periododereferencia"):
        return "Período de referência"
    return None


def _celula_em(celulas: list[str], indice: int | None) -> str:
    """Retorna o texto da célula no índice, ou vazio quando fora da linha."""
    if indice is None or indice >= len(celulas):
        return ""
    return celulas[indice].strip()


def _extrair_provento_duas_colunas(linhas: list[Tag]) -> dict | None:
    """Extrai o provento do layout de duas colunas (Rendimento | Amortização).

    No documento real, a primeira linha mistura pares rótulo/valor de
    identificação com os cabeçalhos ``Rendimento`` e ``Amortização``, e as
    linhas seguintes trazem o rótulo (com ``colspan``) e o valor apenas na
    coluna aplicável. O tipo é decidido pela coluna que contém o valor.
    Retorna ``None`` quando o layout não é reconhecido.
    """
    cabecalho = _localizar_cabecalho_provento(linhas)
    if cabecalho is None:
        return None
    indice, coluna_rendimento, coluna_amortizacao = cabecalho
    linhas_dados = _linhas_dados_provento(
        linhas[indice + 1:], coluna_rendimento, coluna_amortizacao
    )
    limite = min(coluna_rendimento, coluna_amortizacao)
    return _montar_provento_duas_colunas(
        _grade_da_linha(linhas[indice])[:limite], linhas_dados
    )


def _localizar_cabecalho_provento(
    linhas: list[Tag],
) -> tuple[int, int, int] | None:
    """Localiza a linha e as colunas de cabeçalho ``Rendimento``/``Amortização``."""
    for indice, linha in enumerate(linhas):
        rendimento, amortizacao = _indices_colunas_provento(_grade_da_linha(linha))
        if rendimento is not None and amortizacao is not None:
            return indice, rendimento, amortizacao
    return None


def _linhas_dados_provento(
    linhas: list[Tag], coluna_rendimento: int, coluna_amortizacao: int
) -> list[tuple[str, str, str]]:
    """Coleta (chave, valor de rendimento, valor de amortização) por linha."""
    dados: list[tuple[str, str, str]] = []
    for linha in linhas:
        celulas = _grade_da_linha(linha)
        chave = _chave_rotulo_provento(celulas[0]) if celulas else None
        if chave is None:
            continue
        dados.append(
            (
                chave,
                _celula_em(celulas, coluna_rendimento),
                _celula_em(celulas, coluna_amortizacao),
            )
        )
    return dados


def _tipo_rendimento(linhas_dados: list[tuple[str, str, str]]) -> bool | None:
    """Decide se o provento é rendimento pela coluna que contém valor.

    Retorna ``True`` para rendimento, ``False`` para amortização e ``None``
    quando nenhuma coluna tem valor.
    """
    tem_rendimento = any(valor for _chave, valor, _amort in linhas_dados)
    tem_amortizacao = any(amort for _chave, _valor, amort in linhas_dados)
    if not tem_rendimento and not tem_amortizacao:
        return None
    return tem_rendimento and not tem_amortizacao


def _montar_provento_duas_colunas(
    cabecalho: list[str], linhas_dados: list[tuple[str, str, str]]
) -> dict | None:
    """Monta o dicionário do provento decidindo o tipo pela coluna com valor."""
    tipo_rendimento = _tipo_rendimento(linhas_dados)
    if tipo_rendimento is None:
        return None
    resultado = dict(_pares_rotulo_valor(cabecalho))
    for chave, valor_rendimento, valor_amortizacao in linhas_dados:
        valor = valor_rendimento if tipo_rendimento else valor_amortizacao
        if valor:
            resultado[chave] = valor
    resultado["Rendimento"] = "X" if tipo_rendimento else ""
    resultado["Amortização"] = "" if tipo_rendimento else "X"
    return resultado


def _celula_numerica(celula: str) -> bool:
    """Indica se o texto da célula é essencialmente numérico ou monetário."""
    limpo = _normalizar(celula)
    return limpo.isdigit() or (limpo.startswith("r$") and len(limpo) > 2)


def identificar_contexto_tabela(table: Tag) -> str:
    """Identifica o contexto de uma tabela a partir de elementos anteriores."""
    previsto = table.find_previous(["h2", "h3", "h4", "strong", "b", "caption"])
    if previsto is not None:
        contexto = previsto.get_text(strip=True)
        if contexto:
            return contexto
    caption = table.find("caption")
    if caption is not None:
        contexto = caption.get_text(strip=True)
        if contexto:
            return contexto
    return "Informações Gerais"


def identificar_tipo_provento(linha: dict | None) -> str:
    """Identifica se a linha marca o provento como Rendimento ou Amortização."""
    if _tipo_marcado(linha, "rendimento", "Rendimento"):
        return "Rendimento"
    if _tipo_marcado(linha, "amortizacao", "Amortização"):
        return "Amortização"
    return "Não especificado"


def _tipo_marcado(linha: dict | None, chave_normalizada: str, rotulo: str) -> bool:
    """Indica se o rótulo do tipo de provento está marcado com ``X`` na linha."""
    if not linha:
        return False
    for chave, valor in linha.items():
        if _normalizar(chave) == chave_normalizada and str(valor).strip() == "X":
            return True
    return str(linha.get(rotulo, "")).strip() == "X"
