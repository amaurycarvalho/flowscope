import json

import pytest
import responses

from flowscope.domain.structured import (
    CensuraPublica,
    CondicaoExcepcional,
    ProgramaAquisicao,
)
from flowscope.infrastructure.b3 import funds_client as fc
from flowscope.infrastructure.b3.funds_client import B3FundosClient
from flowscope.infrastructure.b3.structured_parser import (
    extrair_censuras,
    extrair_condicoes_excepcionais,
    extrair_programas_aquisicao,
)
from flowscope.infrastructure.cache import CacheManager

_CENSURAS = fc._CENSURAS_URL
_CONDICOES = fc._CONDICOES_URL

CENSURAS_HTML = """<html><body>
<div class="item-censura">
  <h3>FII TORDE EI (TORD)</h3>
  <span class="data">(25/02/2026)</span>
  <p>A B3 S.A. – Brasil, Bolsa, Balcão vem a público censurar a VÓRTIX DISTRIBUIDORA DE TITULOS E VALORES MOBILIARIOS LTDA.</p>
</div>
<div class="item-censura">
  <h3>Companhia Sem Ticker no Titulo</h3>
  <span class="data">(01/03/2026)</span>
  <p>Comunicado de censura sem ticker entre parênteses.</p>
</div>
</body></html>
"""

CENSURAS_SEM_TICKER_HTML = """<html><body>
<div class="item-censura">
  <h3>Emissora XYZ</h3>
  <span class="data">(10/01/2026)</span>
  <p>Censura sem ticker identificável.</p>
</div>
</body></html>
"""

CONDICOES_HTML = """<html><body>
<table>
  <thead>
    <tr>
      <th>Companhia</th>
      <th>Segmento</th>
      <th>Condição Excepcional</th>
      <th>Data da concessão</th>
      <th>Prazo</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Bradsaúde S.A.</td>
      <td>Novo Mercado</td>
      <td>Percentual Mínimo de Ações em Circulação abaixo do requerido</td>
      <td>19/05/2026</td>
      <td>30/10/2027</td>
    </tr>
    <tr>
      <td>Companhia Beta</td>
      <td></td>
      <td>Condição sem prazo</td>
      <td></td>
      <td></td>
    </tr>
  </tbody>
</table>
</body></html>
"""

CONDICOES_COLUNAS_FALTANTES_HTML = """<html><body>
<table>
  <thead>
    <tr>
      <th>Companhia</th>
      <th>Segmento</th>
      <th>Condição Excepcional</th>
      <th>Data da concessão</th>
      <th>Prazo</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Bradsaúde S.A.</td>
      <td>Novo Mercado</td>
      <td>Condição válida</td>
      <td>19/05/2026</td>
      <td>30/10/2027</td>
    </tr>
    <tr>
      <td>Linha incompleta</td>
      <td>Segmento</td>
    </tr>
  </tbody>
</table>
</body></html>
"""


CENSURAS_ACCORDION_HTML = """<html><body>
<ul>
  <li class="accordion-navigation">
    <a href="#panel1">FII TORDE EI (TORD) (25/02/2026)</a>
    <div class="content">
      <p>Primeiro paragrafo da censura.</p>
      <p>Segundo paragrafo da censura.</p>
    </div>
  </li>
  <li class="accordion-navigation">
    <a href="#panel2">SPRINGS (SGPS3)(01/10/2024)</a>
    <div class="content"><p>Outro conteudo.</p></div>
  </li>
</ul>
</body></html>
"""

PROGRAMAS_PAYLOAD = {
    "page": {"pageNumber": 1, "pageSize": 60, "totalRecords": 2, "totalPages": 1},
    "results": [
        {
            "aprrovedDate": "13/08/2026",
            "startDate": "13/08/2026",
            "endDate": "13/02/2028",
            "quantity": "5.000.000 (ON)",
            "company": "3TENTOS (NM)",
            "observation": "Bradesco",
        },
        {
            "aprrovedDate": "07/02/2019",
            "startDate": "08/02/2019",
            "endDate": "31/12/9999",
            "quantity": "1.800.000 (PN)",
            "company": "EMPRESA XPTO (XPTO)",
            "observation": "BTG Pactual",
        },
    ],
}


CONDICOES_CABECALHO_TD_HTML = """<html><body>
<table>
  <tr>
    <td>Companhia</td>
    <td>Segmento</td>
    <td>Condição Excepcional</td>
    <td>Data da concessão</td>
    <td>Prazo para cumprimento</td>
  </tr>
  <tr>
    <td>Bradsaúde S.A.</td>
    <td>Novo Mercado</td>
    <td>Percentual Mínimo de Ações em Circulação abaixo do requerido</td>
    <td>19/05/2026</td>
    <td>30/10/2027</td>
  </tr>
</table>
</body></html>
"""


class TestExtrairProgramas:
    def test_mapeia_campos_do_payload(self):
        programas = extrair_programas_aquisicao(PROGRAMAS_PAYLOAD)
        assert len(programas) == 2
        primeiro = programas[0]
        assert isinstance(primeiro, ProgramaAquisicao)
        assert primeiro.empresa == "3TENTOS (NM)"
        assert primeiro.data_inicio == "13/08/2026"
        assert primeiro.data_fim == "13/02/2028"
        assert primeiro.quantidade == "5.000.000 (ON)"
        assert primeiro.intermediarios == "Bradesco"

    def test_item_sem_empresa_eh_ignorado(self):
        payload = {"results": [{"startDate": "01/01/2026", "company": "  "}]}
        assert extrair_programas_aquisicao(payload) == []

    def test_payload_invalido_retorna_lista_vazia(self):
        assert extrair_programas_aquisicao(None) == []
        assert extrair_programas_aquisicao({"results": "x"}) == []


class TestExtrairCensuras:
    def test_extrai_formato_accordion_da_pagina_real(self):
        censuras = extrair_censuras(CENSURAS_ACCORDION_HTML)
        assert len(censuras) == 2
        primeira = censuras[0]
        assert primeira.titulo == "FII TORDE EI (TORD)"
        assert primeira.ticker == "TORD"
        assert primeira.data == "25/02/2026"
        assert "Primeiro paragrafo" in primeira.conteudo
        assert "Segundo paragrafo" in primeira.conteudo
        segunda = censuras[1]
        assert segunda.ticker == "SGPS3"
        assert segunda.data == "01/10/2024"

    def test_extrai_ticker_data_e_conteudo(self):
        censuras = extrair_censuras(CENSURAS_HTML)
        assert len(censuras) == 2
        primeira = censuras[0]
        assert isinstance(primeira, CensuraPublica)
        assert primeira.titulo == "FII TORDE EI (TORD)"
        assert primeira.ticker == "TORD"
        assert primeira.data == "25/02/2026"
        assert "VÓRTIX" in primeira.conteudo

    def test_titulo_sem_ticker_retorna_none(self):
        censuras = extrair_censuras(CENSURAS_SEM_TICKER_HTML)
        assert len(censuras) == 1
        assert censuras[0].ticker is None
        assert censuras[0].data == "10/01/2026"
        assert "sem ticker" in censuras[0].conteudo

    def test_html_vazio_retorna_lista_vazia(self):
        assert extrair_censuras("<html><body></body></html>") == []
        assert extrair_censuras("") == []


class TestExtrairCondicoesExcepcionais:
    def test_mapeia_cinco_colunas(self):
        condicoes = extrair_condicoes_excepcionais(CONDICOES_HTML)
        assert len(condicoes) == 2
        primeira = condicoes[0]
        assert isinstance(primeira, CondicaoExcepcional)
        assert primeira.companhia == "Bradsaúde S.A."
        assert primeira.segmento == "Novo Mercado"
        assert "Percentual Mínimo" in primeira.condicao
        assert primeira.data_concessao == "19/05/2026"
        assert primeira.prazo == "30/10/2027"

    def test_campos_opcionais_vazios_como_none(self):
        condicoes = extrair_condicoes_excepcionais(CONDICOES_HTML)
        segunda = condicoes[1]
        assert segunda.segmento is None
        assert segunda.data_concessao is None
        assert segunda.prazo is None

    def test_linha_com_colunas_faltantes_eh_ignorada_e_loga_warning(self, caplog):
        with caplog.at_level("WARNING", logger="flowscope.infrastructure.b3.structured_parser"):
            condicoes = extrair_condicoes_excepcionais(CONDICOES_COLUNAS_FALTANTES_HTML)
        assert len(condicoes) == 1
        assert condicoes[0].companhia == "Bradsaúde S.A."
        assert any("2 colunas" in record.getMessage() for record in caplog.records)

    def test_cabecalho_em_td_eh_ignorado(self):
        condicoes = extrair_condicoes_excepcionais(CONDICOES_CABECALHO_TD_HTML)
        assert len(condicoes) == 1
        assert condicoes[0].companhia == "Bradsaúde S.A."

    def test_html_sem_tabela_retorna_lista_vazia(self):
        assert extrair_condicoes_excepcionais("<html><body><p>x</p></body></html>") == []


class TestClientCensurasECondicoes:
    @responses.activate
    def test_listar_censuras_com_cache(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        responses.get(_CENSURAS, body=CENSURAS_HTML, status=200)
        primeira = client.listar_censuras()
        segunda = client.listar_censuras()
        assert len(primeira) == 2
        assert len(segunda) == 2
        assert len(responses.calls) == 1

    @responses.activate
    def test_listar_censuras_pagina_fora_do_ar_lanca_erro(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        responses.get(_CENSURAS, status=500)
        with pytest.raises(RuntimeError, match="censuras públicas"):
            client.listar_censuras()

    @responses.activate
    def test_listar_condicoes_excepcionais_com_cache(self, tmp_path):
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        responses.get(_CONDICOES, body=CONDICOES_HTML, status=200)
        primeira = client.listar_condicoes_excepcionais()
        segunda = client.listar_condicoes_excepcionais()
        assert len(primeira) == 2
        assert len(segunda) == 2
        assert len(responses.calls) == 1

    @responses.activate
    def test_cache_de_condicoes_expira_apos_sete_dias(self, tmp_path):
        meta = tmp_path / "condicoes_excepcionais.json"
        meta.write_text(
            json.dumps(
                {"cached_at": "2020-01-01T00:00:00+00:00", "html": "<html/>"}
            ),
            encoding="utf-8",
        )
        client = B3FundosClient(cache=CacheManager(cache_dir=tmp_path))
        responses.get(_CONDICOES, body=CONDICOES_HTML, status=200)
        condicoes = client.listar_condicoes_excepcionais()
        assert len(condicoes) == 2
        assert len(responses.calls) == 1
