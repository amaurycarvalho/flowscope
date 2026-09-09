"""Estratégias flexíveis de parsing de HTML tabular de documentos da B3."""

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from bs4 import BeautifulSoup, PageElement, Tag


def parse_html(html: str) -> BeautifulSoup:
    """Analisa uma string HTML em um objeto BeautifulSoup."""
    return BeautifulSoup(html, "html.parser")

def extrair_por_rotulo(soup: BeautifulSoup, rotulo: str) -> str | None:
    """Extrai o valor associado a um rótulo textual no HTML.

    Procura o texto do rótulo e captura o valor no mesmo elemento após os
    dois-pontos, no elemento seguinte (irmão) ou no texto restante do
    elemento pai. Retorna ``None`` quando o rótulo não é encontrado.
    """
    rotulo_normalizado = rotulo.strip().lower().rstrip(":")
    fragmento = rotulo.rstrip(":")
    elementos = soup.find_all(
        string=lambda text: fragmento.lower() in text.lower() if text else False
    )
    for elem in elementos:
        texto = str(elem).strip()
        if ":" in texto:
            valor = texto.split(":", 1)[1].strip()
            if valor:
                return valor
        parent = elem.parent
        if parent is None:
            continue
        if isinstance(parent, Tag):
            restante = _texto_apos_no_parent(parent, elem)
            if restante:
                return restante
        valor = _texto_do_proximo_sibling(parent)
        if valor and valor.lower() != rotulo_normalizado:
            return valor
    return None


def _texto_do_proximo_sibling(node: PageElement) -> str | None:
    """Retorna o texto do primeiro elemento irmão subsequente não vazio."""
    atual: PageElement | None = node
    while atual is not None:
        valor = _texto_do_irmao_seguinte(atual)
        if valor:
            return valor
        atual = atual.parent
    return None


def _texto_apos_rotulo(marcador: object, texto_rotulo: str) -> str | None:
    """Extrai o valor imediatamente posterior ao nó do rótulo no HTML."""
    if ":" in texto_rotulo:
        valor = texto_rotulo.split(":", 1)[1].strip()
        if valor:
            return valor
    atual = getattr(marcador, "parent", None)
    visitados: set[int] = set()
    while isinstance(atual, PageElement):
        visitados.add(id(atual))
        restante = _texto_apos_no_parent(atual, atual, visitados)
        if restante:
            return restante
        valor = _texto_do_irmao_seguinte(atual)
        if valor:
            return valor
        atual = atual.parent
    return None


def _texto_do_irmao_seguinte(node: PageElement) -> str | None:
    """Retorna o texto do próximo nó irmão com conteúdo, ignorando espaços."""
    proximo = node.next_sibling
    while proximo is not None:
        if isinstance(proximo, Tag):
            valor = proximo.get_text(" ", strip=True)
        else:
            valor = str(proximo).strip()
        if valor:
            return valor
        proximo = proximo.next_sibling
    return None


def _texto_apos_no_parent(
    parent: Tag, node: PageElement, visitados: set[int] | None = None
) -> str | None:
    """Retorna o texto do elemento pai posterior ao nó informado.

    O nó informado deve ser um filho direto do elemento pai. Nós já
    visitados pelo caminho de busca ascendente são ignorados.
    """
    partes: list[str] = []
    capturar = False
    for conteudo in parent.contents:
        if conteudo is node:
            capturar = True
            continue
        if not capturar:
            continue
        if visitados is not None and isinstance(conteudo, Tag) and id(conteudo) in visitados:
            continue
        if isinstance(conteudo, Tag):
            texto = conteudo.get_text(" ", strip=True)
        else:
            texto = str(conteudo).strip()
        if texto:
            partes.append(texto)
    valor = " ".join(partes).strip()
    return valor or None


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

    if _eh_tabela_rotulo_valor(linhas):
        agrupado: dict[str, str] = {}
        for row in linhas:
            cells = _celulas_da_linha(row)
            agrupado.update(_pares_rotulo_valor(cells))
        return [agrupado] if agrupado else []

    return _linhas_como_dict(linhas, [])


def _celulas_da_linha(row: Tag) -> list[str]:
    """Retorna o texto das células (td ou th) de uma linha de tabela."""
    return [td.get_text(" ", strip=True) for td in row.find_all(["td", "th"])]


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


def _rotulo_em_celula(celula: str) -> bool:
    """Indica se o texto da célula parece um rótulo de campo."""
    if ":" in celula:
        return True
    normalizada = _normalizar(celula)
    palavras = re.split(r"[^a-z0-9]+", normalizada)
    alvos = {
        "nomedofundo",
        "cnpj",
        "codigodenegociacao",
        "administrador",
        "isin",
        "datadainformacao",
        "ano",
        "database",
        "datadopagamento",
        "periododereferencia",
        "valordoprovento",
        "rendimento",
        "amortizacao",
        "tipodeprovento",
        "responsavelpelainformacao",
        "telefonecontato",
    }
    return any(palavra in alvos for palavra in palavras)


def _pares_rotulo_valor(cells: list[str]) -> dict[str, str]:
    """Agrupa as células de uma linha de tabela em pares rótulo→valor."""
    pares: dict[str, str] = {}
    idx = 0
    while idx < len(cells):
        rotulo = cells[idx]
        if _rotulo_em_celula(rotulo):
            if idx + 1 < len(cells):
                pares[rotulo.rstrip(":")] = cells[idx + 1]
            idx += 2
        else:
            idx += 1
    return pares


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
    return rotulo in linha.values() or str(linha.get(rotulo, "")).strip() == "X"


def limpar_valor_monetario(valor: str | None) -> Decimal | None:
    """Limpa uma string monetária brasileira em ``Decimal``."""
    if not valor:
        return None
    texto = valor.replace("R$", "").strip()
    if "," in texto:
        inteiro, _, decimal = texto.partition(",")
        decimal = decimal.replace(",", "")
        texto = f"{inteiro.replace('.', '')}.{decimal}"
    else:
        texto = texto.replace(",", "").replace(".", "")
    try:
        return Decimal(texto or "0")
    except InvalidOperation:
        return None


def converter_data_br_para_iso(data_br: str | None) -> str | None:
    """Normaliza uma data ``DD/MM/AAAA`` para o formato ISO."""
    if not data_br:
        return None
    try:
        return datetime.strptime(data_br.strip(), "%d/%m/%Y").date().isoformat()  # noqa: DTZ007
    except ValueError:
        return data_br.strip()


def extrair_isento_ir(soup: BeautifulSoup) -> bool:
    """Identifica se o provento é isento de IR buscando pelo rótulo indicado."""
    fragmento = "Rendimento isento de IR"
    marcadores = soup.find_all(
        string=lambda text: fragmento.lower() in text.lower() if text else False
    )
    for marcador in marcadores:
        texto_rotulo = str(marcador)
        valor = _texto_apos_rotulo(marcador, texto_rotulo)
        if valor is not None:
            normalizado = _normalizar(valor)
            if "sim" in normalizado and "nao" not in normalizado:
                return True
            if "nao" in normalizado:
                return False
    return False


def extrair_nota_isencao(soup: BeautifulSoup) -> str | None:
    """Extrai a nota de isenção de IR do rodapé do documento."""
    nota = soup.find(
        "p",
        string=lambda text: "Administradora declara" in text if text else False,
    )
    if nota is not None:
        return nota.get_text(strip=True)
    texto = soup.find(
        string=lambda text: "Administradora declara" in text if text else False
    )
    if texto is None:
        return None
    return texto.strip()

def _normalizar(texto: str) -> str:
    """Normaliza texto para comparação de cabeçalhos (minúsculas, sem acentos)."""
    trocas = {
        "ç": "c",
        "á": "a",
        "ã": "a",
        "à": "a",
        "â": "a",
        "é": "e",
        "ê": "e",
        "í": "i",
        "ó": "o",
        "ô": "o",
        "õ": "o",
        "ú": "u",
        ":": "",
        " ": "",
    }
    resultado = texto.strip().lower()
    for origem, destino in trocas.items():
        resultado = resultado.replace(origem, destino)
    return resultado


def extrair_por_regex(html: str, padrao: re.Pattern) -> str | None:
    """Extrai um valor por expressão regular como estratégia de fallback."""
    match = padrao.search(html)
    if match is None:
        return None
    return match.group(1).strip()
