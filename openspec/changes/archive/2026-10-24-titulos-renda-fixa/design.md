## Context

O ramo "Direitos e obrigações" é hoje um placeholder em duas superfícies: `DocumentTreeView._popular_direitos` e `FonteDireitosObrigacoes`. O app já possui a infraestrutura necessária para a mudança:

- `CvmDatasetDownloader` baixa ZIPs anuais da CVM com cache condicional, hash e metadados; `CvmMonthlyDownloader` faz o mesmo para o Informe Mensal de FII.
- A identidade do ticker já é resolvida por `resolver_identidade` (FII) e por `CvmAcionistasSource.obter_cnpj` (companhia via FCA).
- A sub-aba Documentos lê apenas cache; a aquisição é explícita pelo botão "Atualizar" e roda em background (`executar_documentos`).
- O Chat AI é estritamente cache-only e monta a árvore em `MontarArvore`, com manifesto em `manifesto.py`.
- O B3/FNET/RAD e o Plantão já alimentam material facts e notícias; a categoria 48 (Aviso aos Debenturistas) já existe no domínio e no cliente, mas não é adquirida hoje.

Ver `proposal.md` para a motivação e os specs para os requisitos. Este documento fixa as decisões técnicas.

## Goals / Non-Goals

**Goals:**

- Normalizar obrigações (FRE + SECURIT) e direitos (carteira de FII + SECURIT) em um modelo único, com proveniência e cache por ticker.
- Montar a mesma estrutura de árvore na sub-aba Documentos e no Chat AI, com títulos individuais, agregados e `sem-fonte`.
- Manter a aquisição explícita no "Atualizar", internamente separada da aquisição de documentos, idempotente e cache-aware.
- Entregar resumo estruturado + links, sem extração por LLM.

**Non-Goals:**

- `InstrumentRegistration` do BDI da B3 (fase 2).
- Extração/sumarização de eventos por LLM.
- Granularidade por título para CDB/LCI/LCA no lado Obrigações.
- Aquisição automática ao abrir a sub-aba ou durante o Chat AI.
- Mudança de banco de dados ou migração de cache existente.

## Decisions

### 1. CRI/CRA pelo devedor econômico

O vínculo de um CRI/CRA com um ticker é o **CNPJ do devedor econômico do lastro**, não o emissor legal.

- Primário: FRE `outro_valor_mobiliario` da companhia, que já reporta CRI/CRA em que ela é devedora.
- Complemento: SECURIT `cedente_devedor` (`Tipo=Devedor`), usando apenas CNPJs válidos e casando com o CNPJ do ticker.
- O emissor legal (securitizadora) vira metadado do título.

Alternativas descartadas: emissor legal (não reflete a dívida do ticker) e ambos com rótulos distintos (aumentaria a complexidade sem ganho claro).

### 2. Fontes oficiais da CVM como base

- **Obrigações:** `FRE.outro_valor_mobiliario` (debêntures, notas comerciais, letras financeiras, CRI/CRA como devedor).
- **Enriquecimento de CRI/CRA:** `SECURIT.INF_MENSAL_CRI`/`INF_MENSAL_CRA` (LTV, garantias, lastro, subordinação, rating, situação, atrasos, contingências, impacto, desempenho).
- **Direitos de FII:** `INF_TRIMESTRAL/ativo` (CRI/CRA, LCI/LCA por título) e `INF_MENSAL/ativo_passivo` (debêntures e CDB agregados).
- **Eventos e documentos:** material facts (incluindo categoria 48), notícias, FNET/RAD; apenas links, sem extração.

O B3 BDI `InstrumentRegistration` fica para a fase 2: é grande, o emissor é o legal e não o devedor econômico, e os dados da CVM já cobrem o essencial. ANBIMA não entra sem um spike que comprove endpoint público, estabilidade e termos de uso.

### 3. Agregado e ausência de fonte explícitos

- Agregado só quando existe total **por ticker** na fonte: `Debentures` e `Certificados_Deposito_Valores_Mobiliarios` no `INF_MENSAL/ativo_passivo`, sempre na última `Data_Referencia`/`Versao` (nunca somando meses).
- `sem-fonte` para CDB/LCI/LCA no lado Obrigações, pois `InstrumentRegistration` não os lista e `Stock`/`Register` são agregados de mercado sem emissor.
- Ramos vazios mantêm o placeholder atual ("Sem dados de ...") para preservar a estrutura e a navegação.

### 4. Aquisição no "Atualizar", com serviço próprio

O botão "Atualizar" continua sendo o único gatilho, mas o fluxo de trabalho passa a orquestrar duas aquisições separadas:

```text
[Atualizar]
  -> AquisicaoDocumentos.adquirir(ticker, ref, progress, token)
  -> AquisicaoTitulos.adquirir(ticker, ref, progress, token)
  -> resultado combinado + remontagem da árvore
```

- `AquisicaoTitulos` é um serviço de aplicação independente, com progresso e resultado próprios.
- O job de background é único para manter o bloqueio global, mas as etapas são distinguíveis no rótulo ("Documentos" / "Títulos").
- Falha de uma etapa não cancela a outra; o cache válido anterior é preservado.
- Alternativas descartadas: botão separado (mais um controle), automático ao abrir (quebra o modelo cache-only da aba) e junto dos fundamentos (cadências e pesos diferentes).

### 5. Identificadores estáveis e caminhos compactos

Cada título recebe uma chave de fonte determinística e um identificador curto:

- FRE: `CNPJ | Valor_Mobiliario | Identificacao_Valor_Mobiliario | Data_Emissao | Data_Vencimento | Quantidade | Valor`.
- SECURIT: `Codigo_CETIP` ou `Codigo_ISIN`; fallback `CNPJ_Emissora | Codigo_Identificacao_Certificado`.
- Carteira de FII: `Codigo_CETIP` extraído do campo `Emissor`; fallback `CNPJ_Emissor | Emissao | Serie | Data_Vencimento`.
- `id_curto = sha1(chave_fonte)[:10]`.

O caminho usa o `id_curto`; o rótulo humano fica no `nome`/`metadado` do nó. Agregados usam `agregado`; ausência de fonte usa `sem-fonte`. Alternativas descartadas: slug legível (instável e sujeito a colisão) e nome bruto (barras, acentos, tamanho).

### 6. Modelo de domínio

```text
TipoTitulo: DEBENTURE | DEBENTURE_CONVERSIVEL | NOTA_COMERCIAL | CRI | CRA |
            LCI | LCA | CDB | LETRA_FINANCEIRA | OUTRO
PapelTitulo: OBRIGACAO | DIREITO

TituloRendaFixa
  id, tipo, papel, rotulo
  emissor_legal, cnpj_emissor, devedor, cnpj_devedor
  identificacao, emissao, serie, data_emissao, data_vencimento
  indexador, taxa, quantidade, valor, saldo_devedor, valor_posicao
  garantias, caracteristicas, condicao_alteracao
  situacao, rating, contingencias, impacto, desempenho
  ltv, data_ltv
  fonte, data_referencia
  documentos[]

TituloAgregado
  tipo, papel, valor, fonte, data_referencia

AusenciaFonte
  tipo, papel, motivo
```

O modelo é independente de infraestrutura; os adaptadores CVM produzem esses objetos e o cache persiste a forma serializada.

### 7. Cache por ticker

Arquivo `<cache>/direitos-obrigacoes/<TICKER>.json`, escrito atomicamente com `_atomic_write_bytes`:

```json
{
  "ticker": "PETR4",
  "cnpj": "...",
  "tipo_ativo": "acao|fii",
  "assinatura": "sha256(...)",
  "parser_version": "titulos-renda-fixa-v1",
  "adquirido_em": "...",
  "fontes": {
    "fre": {"data_referencia": "...", "arquivo": "...", "hash": "..."},
    "securit_cri": {"data_referencia": "...", "arquivo": "...", "hash": "..."},
    "securit_cra": {"data_referencia": "...", "arquivo": "...", "hash": "..."},
    "fii_ativo": {"data_referencia": "...", "arquivo": "...", "hash": "..."},
    "fii_mensal": {"data_referencia": "...", "arquivo": "...", "hash": "..."}
  },
  "obrigacoes": [],
  "direitos": []
}
```

- A assinatura é derivada do conteúdo normalizado + versão do parser. Sem mudança, reutiliza; com mudança, substitui atomicamente.
- A leitura do cache anterior permite mesclar por fonte e preservar o último valor válido em falha parcial.
- O Chat AI e a GUI leem somente esse arquivo; nenhum dos dois baixa dados.

### 8. Árvore e caminhos

```text
Documentos / Chat AI
  Direitos e obrigações
    data-referencia
    Obrigações
      Títulos
        <tipo>
          <id>/geral
          <id>/adicionais
          <id>/ltv
          <id>/documentos
          agregado/resumo
          sem-fonte
    Direitos
      Títulos
        <tipo> ...
```

No Chat AI, os caminhos canônicos são exatamente esses. Na sub-aba Documentos, os nós usam a mesma hierarquia, com o rótulo humano no nó e a seleção mapeada para o objeto de domínio.

### 9. Apresentação: resumo estruturado + links

- "Informações gerais" e "Informações adicionais" são texto Markdown montado a partir dos campos normalizados.
- "LTV" só aparece quando a fonte informa `Indice_LTV` (CRI); caso contrário, "LTV: não informado".
- "Documentos relacionados" lista links de material facts/notícias já cacheados e URLs oficiais CVM/B3.
- Nada é baixado, extraído ou resumido ao selecionar um título; o botão "Abrir documento" continua restrito a arquivos.

### 10. Assinatura do manifesto do Chat AI

O manifesto invalida quando o estado muda. Os arquivos JSON de títulos dos tickers da watchlist DEVEM entrar na lista de `caminhos` passada a `MontarArvore.montar` (GUI e CLI/MCP), para que a assinatura mude quando um título é adquirido ou atualizado. O mapa do manifesto ganha os padrões de caminho do ramo e uma linha de playbook; apenas ramos existentes são anunciados.

## Risks / Trade-offs

- **Mudança de schema nos datasets CVM** → validar colunas obrigatórias, versionar o parser e degradar com `sem-fonte`/cache anterior em vez de quebrar a árvore.
- **Tamanho e latência dos ZIPs (FRE, SECURIT, FII)** → cache condicional por ano, filtro por CNPJ, progresso e cancelamento; não baixar no Chat AI.
- **Qualidade do `cedente_devedor` (CNPJs inválidos, SPEs)** → normalizar e validar CNPJ; casar apenas com o CNPJ do ticker; não criar vínculo por nome ou aproximação.
- **FRE com CRI/CRA mislabels ou poucas companhias** → tratar como fonte de obrigações reportadas; complementar com SECURIT; explicitar a ausência quando não houver vínculo.
- **CDB/LCI/LCA sem fonte por emissor** → nó `sem-fonte` explícito; não usar agregado de mercado como se fosse do ticker.
- **Manifesto acima de 4K tokens** → anunciar apenas os caminhos presentes e manter a descrição compacta; usar `listar` para os rótulos humanos.
- **Complexidade da árvore da GUI** → separar a renderização em módulo de aplicação e manter o `DocumentFlowMixin` focado no fluxo de documentos.
- **Cache desatualizado por falha parcial** → preservar o último cache válido por fonte e registrar a data de referência no nó de proveniência.

## Migration Plan

1. Adicionar o novo modelo, parsers e cache sem alterar os caminhos atuais do ramo.
2. Estender a árvore da GUI e do Chat AI; quando não houver cache, manter os placeholders atuais.
3. Estender o botão "Atualizar" para orquestrar `AquisicaoTitulos`, com progresso separado.
4. Atualizar os testes existentes do ramo placeholder e do manifesto; adicionar testes dos novos parsers/joins/cache.
5. Rollback: reverter o código para o placeholder; os arquivos `<cache>/direitos-obrigacoes/*.json` são aditivos e podem ser ignorados/removidos sem migração.

## Open Questions

- Paridade de aquisição na CLI/MCP: o Chat AI/MCP já lê o cache populado pela GUI; um subcomando `carregar titulos` é desejável, mas pode ficar para uma change futura.
- Tratamento visual dos links (clicáveis versus texto) pode ser decidido na implementação, desde que a abertura externa funcione.
- Mapeamento de tipos exóticos (CDCA, CFF, NC) para `OUTRO` pode ser refinado depois, sem alterar os caminhos nem o cache.
