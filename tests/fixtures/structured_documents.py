FLAT_HTML = """<html><head><meta charset="utf-8"></head><body>
<h3>Rendimentos e Amortizações</h3>
<table>
  <tr>
    <td class="rotulo">Nome do Fundo:</td>
    <td><span>ALIANZA TRUST RENDA IMOBILIÁRIA - FUNDO DE INVESTIMENTO IMOBILIÁRIO</span></td>
  </tr>
  <tr>
    <td class="rotulo">CNPJ do Fundo:</td>
    <td><span>28.737.771/0001-85</span></td>
  </tr>
  <tr>
    <td class="rotulo">Nome do Administrador:</td>
    <td><span>BTG PACTUAL SERVIÇOS FINANCEIROS S/A DTVM</span></td>
  </tr>
  <tr>
    <td class="rotulo">CNPJ do Administrador:</td>
    <td><span>59.281.253/0001-23</span></td>
  </tr>
  <tr>
    <td class="rotulo">Responsável pela Informação:</td>
    <td><span>Leandro Pereira</span></td>
  </tr>
  <tr>
    <td class="rotulo">Telefone Contato:</td>
    <td><span>(11) 3383-3102</span></td>
  </tr>
  <tr>
    <td class="rotulo">Data da Informação:</td>
    <td><span>18/06/2026</span></td>
  </tr>
  <tr>
    <td class="rotulo">Ano:</td>
    <td><span>2026</span></td>
  </tr>
  <tr>
    <td class="rotulo">Código ISIN:</td>
    <td><span>BRALZRCTF006</span></td>
  </tr>
  <tr>
    <td class="rotulo">Código de negociação:</td>
    <td><span>ALZR11</span></td>
  </tr>
  <tr>
    <td class="rotulo">Rendimento</td>
    <td><span>X</span></td>
  </tr>
  <tr>
    <td class="rotulo">Amortização</td>
    <td><span></span></td>
  </tr>
  <tr>
    <td class="rotulo">Data-base:</td>
    <td><span>18/06/2026</span></td>
  </tr>
  <tr>
    <td class="rotulo">Valor do provento (R$/unidade):</td>
    <td><span>R$ 0,08355</span></td>
  </tr>
  <tr>
    <td class="rotulo">Data do pagamento:</td>
    <td><span>25/06/2026</span></td>
  </tr>
  <tr>
    <td class="rotulo">Período de referência:</td>
    <td><span>Maio-2026</span></td>
  </tr>
</table>
<p><strong>Rendimento isento de IR*:</strong> Sim</p>
<p>A Administradora declara que o Fundo de Investimento Imobiliário se enquadra no inciso III do art. 3º da Lei 11.033/2004.</p>
</body></html>
"""

TABLE_HTML = """<html><body>
<h3>Detalhes do Provento</h3>
<table>
  <thead>
    <tr>
      <th>Código ISIN</th>
      <th>Código de negociação</th>
      <th>Data-base</th>
      <th>Valor do provento (R$/unidade)</th>
      <th>Data do pagamento</th>
      <th>Período de referência</th>
      <th>Rendimento</th>
      <th>Amortização</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>BRALZRCTF006</td>
      <td>ALZR11</td>
      <td>18/06/2026</td>
      <td>0,08355</td>
      <td>25/06/2026</td>
      <td>Maio-2026</td>
      <td>X</td>
      <td></td>
    </tr>
  </tbody>
</table>
<p><strong>Rendimento isento de IR*:</strong> Não</p>
</body></html>
"""

AMORTIZACAO_HTML = """<html><body>
<table>
  <thead>
    <tr>
      <th>Código ISIN</th>
      <th>Código de negociação</th>
      <th>Rendimento</th>
      <th>Amortização</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>BRALZRCTF006</td>
      <td>ALZR11</td>
      <td></td>
      <td>X</td>
    </tr>
  </tbody>
</table>
</body></html>
"""

SEM_DADOS_HTML = """<html><body><p>Documento sem conteúdo tabular.</p></body></html>"""
