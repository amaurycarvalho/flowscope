## Context

Ver `proposal.md` — Why. O estado atual relevante:

- Dois extrators de PDF duplicados: `application/document_preview.texto_de_pdf` e
  `infrastructure/b3/bdr/text.extrair_texto`, ambos com `except Exception -> ""`.
- O marcador `SEM_TEXTO`/`tem_texto` existe em dois módulos (application e domain),
  com importadores divididos entre os dois.
- `DocumentFlowMixin.preparar_texto` é o gargalo único de extração+cache dos dois
  painéis e hoje grava `texto or SEM_TEXTO` sempre que não há hit.
- Notícias resolvem o documento vinculado em `infrastructure/b3/noticias_vinculo.py`,
  hoje `baixar_conteudo_vinculado(texto) -> str | None`, injetado no painel como
  `Callable[[str], str | None]` (`app_wiring.py`).
- A regra de camadas (`tests/architecture/guardrail.py`) permite
  `infrastructure -> application` e proíbe `application -> infrastructure`.

## Goals / Non-Goals

**Goals:**

- Um único extrator de PDF, resiliente e com resultado tipado.
- Diferir ausência real de parcial, falha e proteção, com cache correto.
- Recuperar PDFs protegidos via diálogo de senha no preview interativo, em
  **Documentos e no documento vinculado das Notícias**.
- Anotar texto parcial e retentá-lo **automaticamente** (nova seleção/clique no
  documento e "Resumir pendentes"), sem controle dedicado.
- Manter `bdr/text.extrair_texto` com assinatura `bytes -> str`.

**Non-Goals:**

- Persistir a senha ou qualquer credencial.
- Trocar a biblioteca de PDF ou mudar o schema do cache de texto.
- Migrar/limpar marcadores `SEM_TEXTO` já gravados por falhas antigas.
- Botão de "Tentar novamente": a retentativa é implícita.
- Configurar o limite de tentativas por arquivo de preferências (basta ser
  parametrizável na construção).

## Decisions

### 1. Resultado tipado na camada de aplicação

Criar em `application/document_preview.py`:

```python
class StatusExtracao(Enum):
    OK = "ok"                # texto completo
    PARCIAL = "parcial"      # texto não vazio + páginas com falha
    SEM_TEXTO = "sem_texto"  # leu, não há texto (escaneado)
    FALHA = "falha"          # abertura/parse/OSError/RecursionError
    PROTEGIDO = "protegido"  # criptografado que não abriu

@dataclass(frozen=True)
class ExtracaoTexto:
    texto: str
    status: StatusExtracao
    paginas_com_falha: int = 0
```

Funções: `extrair_pdf(dados, senha=None) -> ExtracaoTexto` e
`extrair_arquivo(caminho, seletor=None, senha=None) -> ExtracaoTexto`. Mantém-se
`texto_de_pdf(...) -> str` como adaptador de compatibilidade.

- **Por quê:** o cache e a apresentação precisam distinguir os cinco estados; um
  `str` não distingue ausência de parcial nem de falha.
- **Alternativas:** `str | None` (perde distinção); exceções tipadas (o log já cobre
  a tipagem e forçaria tratamento em todos os call sites).

### 2. Onde o extrator unificado mora

O extrator vive em `application/document_preview.py`, e
`infrastructure/b3/bdr/text.extrair_texto` passa a delegar:

```python
def extrair_texto(dados_pdf: bytes) -> str:
    return extrair_pdf(dados_pdf).texto
```

- **Por quê:** a regra de camadas permite `infrastructure -> application`, mas não
  o inverso; a application já contém a extração de HTML/preview.
- **Alternativas:** mover para `domain` (proibido: domínio é puro, sem terceiros);
  manter dois extrators (divergem).

### 3. Resiliência: tolerância por página

`PdfReader`/abertura protegidos por `try`; cada página extraída em `try`
individual, acumulando `paginas_com_falha`. Texto vazio com todas as páginas
falhas → `FALHA`; texto vazio com páginas lidas → `SEM_TEXTO`; texto não vazio com
falhas → `PARCIAL`; sem falhas → `OK`.

- **Por quê:** hoje uma página ruim descarta o documento inteiro.
- **Alternativas:** abortar ao primeiro erro (perde texto útil).

### 4. Criptografia e senha

Se `reader.is_encrypted`, tentar `reader.decrypt("")`. Sem sucesso e sem senha →
`PROTEGIDO`. Com senha, tentar `reader.decrypt(senha)`; sem sucesso → `PROTEGIDO`.
`DependencyError`/falhas inesperadas no decrypt caem em `PROTEGIDO`. A senha
transita apenas em memória, nunca é persistida nem logada.

- **Por quê:** a maioria dos PDFs "protegidos" da B3 abre com senha vazia; e o
  usuário pode conhecer a senha real.
- **Alternativas:** sempre `PROTEGIDO` (perde recuperação); guardar senha (risco).

### 5. Senha no documento vinculado das Notícias

`baixar_conteudo_vinculado` passa a devolver `ExtracaoTexto | None` e a aceitar
`senha`:

```python
def baixar_conteudo_vinculado(
    texto: str, *, senha: str | None = None, sessao=None, timeout=TIMEOUT
) -> ExtracaoTexto | None: ...
```

O ramo PDF usa `extrair_pdf(bruto, senha)`; o ramo HTML produz
`ExtracaoTexto(texto, OK|SEM_TEXTO)`. `None` continua significando "não resolvido"
(sem URL, host não suportado, captcha, falha) — o corpo original é mantido.
`PROTEGIDO` deixa de ser colapsado em `None` para que o painel possa pedir a
senha. O callable injetado no painel muda de `Callable[[str], str | None]` para
`Callable[[str, str | None], ExtracaoTexto | None]` (ajuste em `app_wiring.py` e
`app_tab_layout.py`).

- **Por quê:** sem propagar o status, o painel não distingue "protegido" de "não
  resolvido" e não sabe quando pedir senha.
- **Alternativas:** manter `str` e sinalizar proteção por exceção (inverte o fluxo
  e escapa do tratamento tolerante atual).
- **Trade-off:** cada tentativa com senha refaz o download do vinculado (limitado
  a 3). Otimizar cacheando os bytes da sessão fica como melhoria futura.

### 6. Semântica de cache e memoização em `preparar_texto`

`_texto_do_arquivo` passa a devolver `ExtracaoTexto`. `preparar_texto` grava no
store apenas quando o status é `OK` ou `SEM_TEXTO`; `PARCIAL`, `FALHA` e
`PROTEGIDO` NÃO são persistidos. Na sessão, apenas resultados **definitivos**
(`OK`/`SEM_TEXTO`) são memoizados em `_preview_cache`; os **não definitivos** não
são guardados, de modo que qualquer nova pré-visualização do mesmo documento
reconverte o arquivo sem exigir nenhum controle extra.

- **Por quê:** impede que um resultado não definitivo vire permanente e faz a
  retentativa ser automática, sem botão.
- **Alternativas:** memoizar o não definitivo e exigir ação explícita (rejeitado
  pelo requisito); gravar marcador volátil (polui o contrato do store).

### 7. Parcial: anotação, sem resumo, retry automático

No preview, um resultado `PARCIAL` DEVE exibir uma anotação com o número de
páginas não extraídas (ex.: `[Texto parcial: N página(s) não pôde(ram) ser
extraída(s).]`) antes do conteúdo. O texto parcial NÃO DEVE gerar resumo: o
documento permanece pendente (`long_summary is None`). A retentativa é
**automática** e ocorre em dois gatilhos:

```
(a) nova pré-visualização do documento
      - seleção de outro item e volta
      - clique no MESMO documento já selecionado
        (o <<TreeviewSelect>> não dispara; o painel trata o clique
         no documento selecionado quando o último status não é definitivo)

(b) "Resumir pendentes"
      - o lote reconverte os pendentes; parcial/falha/protegido não têm
        cache nem resumo, então são naturalmente retentados
```

- **Por quê:** o requisito é retry implícito; sem botão e sem estado de "tentar
  de novo" na UI.
- **Alternativas:** botão dedicado (rejeitado); re-seleção apenas via troca de item
  (menos descobrível).

### 8. Lote: utilização e retentativa

O lote DEVE decidir o que resumir pelo **status**, não só por "tem texto":
apenas `OK` (completo) é resumível. `PARCIAL`, `FALHA` e `PROTEGIDO` são pulados e
permanecem pendentes, sendo retentados no próximo "Resumir pendentes". Para o
`NoticiasPanel`, o gancho `texto_utilizavel` continua cobrindo apontador não
resolvido e passa a excluir os estados não definitivos.

- **Por quê:** resumir parcial/instável consolidaria conteúdo incompleto e
  impediria o reprocessamento posterior.
- **Alternativas:** resumir o parcial (rejeitado pela decisão 7).

### 9. Diálogo de senha e limite de tentativas

Seam `_solicitar_senha(arquivo) -> str | None` no `DocumentFlowMixin`, com padrão
`None` (headless/lote). `DocumentTreePanel` e `NoticiasPanel` implementam com um
diálogo modal (`simpledialog.askstring(..., show="*")`). O limite é
`MAX_TENTATIVAS_SENHA = 3`, parametrizável no construtor dos painéis
(`senha_max_tentativas: int = 3`). O contador é por documento/seleção e reinicia a
cada novo preview (nova seleção ou clique no mesmo documento). Ao esgotar, o
sistema informa e para de solicitar, exibindo o melhor conteúdo disponível
(corpo/apontador ou ausência). Fluxo:

```
worker extrai -> PROTEGIDO
        |
   Tk (_aplicar_preview): painel interativo?
        | sim
   tentativas < 3 ?
        | sim                              | não
   _solicitar_senha() --cancelar--> exibe melhor conteúdo
        | senha
   re-submete worker com senha -> OK grava+exibe
                                \-> PROTEGIDO -> avisa e re-solicita
```

- **Por quê:** a senha é interação de UI; o worker nunca abre diálogo e o lote
  permanece não interativo.
- **Alternativas:** perguntar no worker (proibido: sem widgets fora da thread do
  Tk); loop sem limite (fadiga do usuário).

### 10. Unificação do marcador

`SEM_TEXTO`/`tem_texto` passam a viver só em `domain/documents/texto.py`;
`application/document_preview` re-exporta para não quebrar importadores e testes.

- **Por quê:** valores idênticos hoje, mas com dois donos — divergem no próximo
  ajuste.
- **Alternativas:** manter a duplicação (custo de consistência).

## Risks / Trade-offs

- [Retorno de `_texto_do_arquivo`/`_baixar_vinculo` muda] → quebra override do
  `NoticiasPanel`, wiring e monkeypatches de teste; atualizar código e testes no
  mesmo passo.
- [Reconversão a cada nova visualização de não definitivo] → é o comportamento
  desejado (retry), mas pode rebaixar rede nas Notícias; mitigado pelo limite de
  senha e por os não definitivos serem minoria.
- [Clique no mesmo nó não dispara seleção] → tratar `<Button-1>`/clique no
  documento selecionado para re-submeter a pré-visualização.
- [Diálogo em thread errada] → solicitar só em `_aplicar_preview` (thread do Tk) e
  re-submeter a extração ao background.
- [Resultado obsoleto de senha] → reaproveitar o descarte por seleção/`req_id`.
- [Backend criptográfico ausente] → tratar `DependencyError` como `PROTEGIDO`.
- [Marcadores antigos envenenados] → sem migração automática; limpeza manual.

## Migration Plan

- Sem migração de dados. Deploy é a troca de código; rollback é reverter a change.
  Entradas `SEM_TEXTO` gravadas antes desta change continuam válidas e não são
  reavaliadas automaticamente.

## Open Questions

- Cachear em memória os bytes do documento vinculado para não rebaixar a cada
  nova tentativa de senha (otimização). Não muda specs nem abordagem.
- Prefixo textual exato da anotação de parcial (texto final a definir na
  implementação). Não muda specs nem abordagem.
