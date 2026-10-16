"""Interface de linha de comando do FlowScope."""

import argparse
import json
import sys
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from flowscope.domain.structured import DocumentoProvento


def build_parser() -> argparse.ArgumentParser:
    """Constrói o parser de argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        prog="flowscope",
        description=(
            "Plataforma open source de análise de ativos da B3: fluxo de ordens, "
            "fundamentos de ações e FIIs, documentos e notícias regulatórias, com IA opcional"
        ),
        epilog="Documentação: https://github.com/amaurycarvalho/flowscope",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Abrir interface gráfica",
    )
    parser.add_argument(
        "--tickers",
        type=str,
        metavar="ARQUIVO",
        help="Arquivo texto com lista de tickers (um por linha)",
    )
    parser.add_argument(
        "--vwap",
        action="store_true",
        help="Exportar VWAP em CSV",
    )
    parser.add_argument(
        "--structured-earnings",
        type=str,
        metavar="TICKER",
        help="Extrair rendimentos e amortizações estruturados do ticker",
    )
    parser.add_argument(
        "--data-inicio",
        type=_parse_data,
        metavar="AAAA-MM-DD",
        help="Data de início da consulta de proventos",
    )
    parser.add_argument(
        "--data-fim",
        type=_parse_data,
        metavar="AAAA-MM-DD",
        help="Data de fim da consulta de proventos",
    )
    parser.add_argument(
        "--output",
        type=str,
        metavar="ARQUIVO",
        help="Arquivo JSON de saída da extração estruturada",
    )
    parser.add_argument(
        "--fatos-relevantes",
        type=str,
        metavar="TICKER",
        help="Extrair fatos relevantes, assembleias e avisos do ticker via GetMaterialFacts",
    )
    parser.add_argument(
        "--noticias",
        action="store_true",
        help="Listar notícias do Plantão B3",
    )
    parser.add_argument(
        "--regulacao",
        action="store_true",
        help="Extrair censuras públicas e condições excepcionais da B3",
    )
    parser.add_argument(
        "--categoria",
        type=str,
        metavar="CODIGO",
        help=(
            "Filtrar categoria de documento para --fatos-relevantes "
            "(1=Assembleias, 3=Aviso Acionistas, 4=Fatos Relevantes, "
            "48=Aviso Debenturistas, 107=Relatório Proventos)"
        ),
    )
    parser.add_argument(
        "--palavra",
        type=str,
        metavar="TERMO",
        help="Filtrar notícias por palavra-chave (usado com --noticias)",
    )

    parser.add_argument(
        "--version",
        action="store_true",
        help="Exibir versão",
    )
    parser.add_argument(
        "--create-shortcut",
        action="store_true",
        help="Criar atalho no desktop (Linux)",
    )
    parser.add_argument(
        "--mcp",
        action="store_true",
        help="Iniciar o servidor MCP (stdio) do FlowScopeBR",
    )
    _adicionar_subcomandos_nav(parser)
    return parser


def _adicionar_subcomandos_nav(parser: argparse.ArgumentParser) -> None:
    """Registra o subcomando ``nav`` com as operações de navegação."""
    subcomandos = parser.add_subparsers(dest="comando")
    nav = subcomandos.add_parser(
        "nav",
        help="Executar operações de navegação da árvore de conhecimento",
    )
    operacoes = nav.add_subparsers(dest="operacao")
    listar = _subparser_nav(operacoes, "listar")
    listar.add_argument("--cursor", type=str, metavar="TOKEN", help="Continuar a paginação")
    _subparser_nav(operacoes, "contar")
    _subparser_nav(operacoes, "existe")
    obter = _subparser_nav(operacoes, "obter")
    obter.add_argument("--offset", type=int, metavar="N", help="Deslocamento em caracteres")
    obter.add_argument("--limite", type=int, metavar="N", help="Caracteres por página")
    buscar = _subparser_nav(operacoes, "buscar")
    buscar.add_argument("--regex", type=str, required=True, help="Expressão regular")
    buscar.add_argument("--em", type=str, metavar="CAMPOS", help="Campos separados por vírgula")
    buscar.add_argument("--max", type=int, metavar="N", help="Máximo de resultados")
    buscar.add_argument("--cursor", type=str, metavar="TOKEN", help="Continuar a paginação")
    semantico = _subparser_nav(operacoes, "buscar-semantico")
    semantico.add_argument("--consulta", type=str, required=True, help="Texto da consulta")
    semantico.add_argument("--max", type=int, metavar="N", help="Máximo de resultados")
    semantico.add_argument("--cursor", type=str, metavar="TOKEN", help="Continuar a paginação")
    _subparser_nav(operacoes, "manifesto")


def _subparser_nav(
    operacoes: argparse._SubParsersAction, nome: str
) -> argparse.ArgumentParser:
    """Cria um subparser de operação ``nav`` com caminho e ``--pretty``."""
    sub = operacoes.add_parser(nome, help=f"Operação nav {nome}")
    if nome != "manifesto":
        sub.add_argument("caminho", type=str, help="Caminho canônico do nó")
    sub.add_argument(
        "--pretty", action="store_true", help="Formatar a saída JSON para leitura humana"
    )
    return sub



def _parse_data(valor: str) -> date:
    """Interpreta o argumento de data no formato ``AAAA-MM-DD``."""
    try:
        return date.fromisoformat(valor)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Data inválida: {valor!r} (use o formato AAAA-MM-DD)"
        ) from None


def _load_tickers(path: str) -> list[str]:
    filepath = Path(path)
    if not filepath.exists():
        print(f"Erro: arquivo de tickers não encontrado: {path}", file=sys.stderr)
        sys.exit(1)
    tickers = [
        line.strip().upper()
        for line in filepath.read_text().splitlines()
        if line.strip()
    ]
    if not tickers:
        print(f"Erro: arquivo de tickers está vazio: {path}", file=sys.stderr)
        sys.exit(1)
    return tickers


def run_cli(args: argparse.Namespace) -> None:
    """Executa a análise dos tickers informados e exibe os resultados."""
    from flowscope.application.use_cases import AnalyzeTickersUseCase
    from flowscope.infrastructure.b3.client import B3Client
    from flowscope.infrastructure.b3.repository import B3DataRepository

    repo = B3DataRepository(B3Client())
    ref_date = datetime.now(timezone.utc).date()

    tickers = None
    if args.tickers:
        tickers = _load_tickers(args.tickers)

    use_case = AnalyzeTickersUseCase(repo)
    result = use_case.execute(ref_date, tickers)

    if not result:
        print("Nenhum dado disponível para o período.")
        return

    print("=== FlowScopeBR - Análise de Indicadores ===")
    print(f"Data de referência: {ref_date}")
    print()
    for ticker, data in result.items():
        vwap_info = data.get("vwap")
        cvd_info = data.get("cvd")
        if vwap_info:
            print(f"{ticker}: VWAP={vwap_info['period_vwap']:.4f}")
        if cvd_info:
            print(f"{ticker}: CVD={cvd_info['accumulated_cvd']:.2f}")


def export_vwap_csv(
    tickers: list[str],
    metrics: dict,
    output_path: str | None = None,
) -> str:
    """Gera o conteúdo CSV com o VWAP por ticker e opcionalmente grava em arquivo."""
    lines = ["Ticker;VWAP_Periodo"]
    for ticker in tickers:
        data = metrics.get(ticker, {}).get("vwap")
        if data:
            lines.append(f"{ticker};{data['period_vwap']}")
    content = "\n".join(lines)
    if output_path:
        Path(output_path).write_text(content, encoding="utf-8")
    return content


def run_structured_earnings(args: argparse.Namespace) -> list[DocumentoProvento]:
    """Executa a extração estruturada de proventos do ticker informado."""
    from flowscope.application.structured_use_cases import ExtrairProventosUseCase
    from flowscope.infrastructure.b3.funds_client import B3FundosClient
    from flowscope.infrastructure.b3.structured_repository import FundosRepository

    ticker = args.structured_earnings.upper()
    repo = FundosRepository(B3FundosClient())
    use_case = ExtrairProventosUseCase(repo)
    documentos = use_case.execute(
        ticker,
        data_inicio=args.data_inicio,
        data_fim=args.data_fim,
        progress_callback=_progresso,
    )

    if args.output:
        Path(args.output).write_text(
            json.dumps(
                [d.to_dict() for d in documentos],
                indent=2,
                ensure_ascii=False,
                default=_json_default,
            ),
            encoding="utf-8",
        )
        if documentos:
            print(f"Extração concluída: {len(documentos)} provento(s) em {args.output}")
    else:
        if not documentos:
            print(f"Nenhum dado disponível para {ticker}")
        else:
            print(
                json.dumps(
                    [d.to_dict() for d in documentos],
                    indent=2,
                    ensure_ascii=False,
                    default=_json_default,
                )
            )
    return documentos


def run_fatos_relevantes(args: argparse.Namespace) -> dict:
    """Executa a extração de fatos relevantes do ticker via ``GetMaterialFacts``."""
    from flowscope.application.structured_use_cases import (
        ExtrairDadosRegulatoriosUseCase,
    )
    from flowscope.infrastructure.b3.funds_client import B3FundosClient

    use_case = ExtrairDadosRegulatoriosUseCase(B3FundosClient())
    resultado = use_case.execute(
        "fatos",
        ticker=args.fatos_relevantes.upper(),
        categoria=args.categoria,
        data_inicio=args.data_inicio,
        data_fim=args.data_fim,
    )
    _imprimir_json(resultado)
    return resultado


def run_noticias(args: argparse.Namespace) -> dict:
    """Executa a listagem de notícias do Plantão B3."""
    from flowscope.application.structured_use_cases import (
        ExtrairDadosRegulatoriosUseCase,
    )
    from flowscope.infrastructure.b3.funds_client import B3FundosClient

    use_case = ExtrairDadosRegulatoriosUseCase(B3FundosClient())
    resultado = use_case.execute(
        "noticias",
        agencia="18",
        palavra=args.palavra,
        data_inicio=args.data_inicio,
        data_fim=args.data_fim,
    )
    _imprimir_json(resultado)
    return resultado


def run_regulacao(args: argparse.Namespace) -> dict:
    """Executa a extração de censuras públicas e condições excepcionais."""
    from flowscope.application.structured_use_cases import (
        ExtrairDadosRegulatoriosUseCase,
    )
    from flowscope.infrastructure.b3.funds_client import B3FundosClient

    use_case = ExtrairDadosRegulatoriosUseCase(B3FundosClient())
    resultado = use_case.execute("regulacao")
    _imprimir_json(resultado)
    return resultado


def _imprimir_json(dados: dict) -> None:
    """Exibe um dicionário como JSON formatado no stdout."""
    print(
        json.dumps(
            dados,
            indent=2,
            ensure_ascii=False,
            default=_json_default,
        )
    )


def _progresso(mensagem: str, erro: bool) -> None:
    """Exibe o progresso da extração em stderr, sem poluir a saída JSON."""
    prefixo = "ERRO: " if erro else ""
    print(f"{prefixo}{mensagem}", file=sys.stderr)


def executar_nav(args: argparse.Namespace) -> None:
    """Executa uma operação ``nav`` e imprime o JSON em stdout.

    Erros de domínio recuperáveis são impressos como JSON estruturado em
    ``stdout``; o diagnóstico vai para ``stderr`` e o processo encerra com
    código 1.
    """
    from flowscope.presentation.navegacao import conteudo

    core = montar_core_navegacao()
    operacao = _operacao_nav(args.operacao)
    campos = _campos_nav(args)
    resultado = core.executar(operacao, campos)
    if resultado.erro is not None:
        _imprimir_nav(resultado.erro, args.pretty)
        print(
            f"Erro de navegação ({resultado.erro['motivo']}): "
            f"{resultado.erro.get('detalhe', '')}",
            file=sys.stderr,
        )
        sys.exit(1)
    _imprimir_nav(conteudo(resultado.dados), args.pretty)


def _operacao_nav(operacao: str | None) -> str:
    """Traduz o nome do subcomando para a operação canônica do núcleo."""
    if operacao == "buscar-semantico":
        return "buscar_semantico"
    return operacao or ""


def _campos_nav(args: argparse.Namespace) -> dict:
    """Monta os campos da operação a partir dos argumentos do subcomando."""
    campos: dict = {}
    if getattr(args, "caminho", None) is not None:
        campos["caminho"] = args.caminho
    for chave in ("cursor", "offset", "limite", "regex", "consulta", "max"):
        valor = getattr(args, chave, None)
        if valor is not None:
            campos[chave] = valor
    em = getattr(args, "em", None)
    if em:
        campos["em"] = [parte.strip() for parte in em.split(",") if parte.strip()]
    return campos


def _imprimir_nav(dados: object, pretty: bool) -> None:
    """Imprime o resultado da navegação como JSON em stdout."""
    print(
        json.dumps(
            dados,
            indent=2 if pretty else None,
            ensure_ascii=False,
            default=_json_default,
        )
    )


def montar_core_navegacao() -> object:
    """Ponto de composição headless da navegação sobre o cache local padrão.

    Monta a mesma árvore de conhecimento do chat a partir do cache local —
    conhecimento do FlowScope, fundamentos, documentos, notícias, guidance e
    direitos/obrigações — e a embrulha no ``NavegacaoCore`` reusado pela CLI e
    pelo servidor MCP.
    """
    from flowscope import __release_date__, __version__
    from flowscope.application.chat.conhecimento import (
        FonteConhecimento,
        estrutura_conhecimento,
    )
    from flowscope.application.chat.direitos_obrigacoes import FonteDireitosObrigacoes
    from flowscope.application.chat.documentos import FonteDocumentos
    from flowscope.application.chat.fundamentos import FonteFundamentos
    from flowscope.application.chat.guidance import FonteGuidance
    from flowscope.application.chat.montar import MontarArvore
    from flowscope.application.chat.noticias import FonteNoticias
    from flowscope.application.navegacao.core import NavegacaoCore
    from flowscope.infrastructure.cache import CacheManager
    from flowscope.presentation.gui.app_tabs import TAB_CONTENT
    from flowscope.presentation.gui.app_wiring import (
        montar_adaptadores_documentos,
        montar_adaptadores_noticias,
    )
    from flowscope.presentation.gui.widgets.about_panel import (
        APRESENTACAO,
        LICENCA,
        REPOSITORIO_URL,
    )

    base = CacheManager().get_cache_dir()
    documentos = montar_adaptadores_documentos(base)
    noticias = montar_adaptadores_noticias(base)
    watchlist = _watchlist_config()
    abas, subabas = estrutura_conhecimento(TAB_CONTENT)
    fontes = [
        FonteConhecimento(
            {
                "apresentacao": APRESENTACAO,
                "licenca": LICENCA,
                "versao": __version__,
                "release_date": __release_date__,
                "repositorio": REPOSITORIO_URL,
            },
            abas=abas,
            subabas=subabas,
        ),
        FonteFundamentos(_carregar_fundamentos(watchlist), watchlist=watchlist),
        FonteDocumentos(
            catalog=documentos.catalogo, rg_chaves=_rg_chaves(documentos)
        ),
        FonteDireitosObrigacoes(),
        FonteNoticias(catalog=noticias.catalogo),
        FonteGuidance(watchlist, documentos.guidance_service, documentos.catalogo),
    ]
    arvore = MontarArvore(fontes).montar(
        caminhos=_guidance_paths(documentos, watchlist), watchlist=watchlist
    )
    return NavegacaoCore(arvore)


def _watchlist_config() -> list[str]:
    """Lê a última watchlist persistida no ``config.json`` do usuário."""
    from flowscope.infrastructure.llm.config import CONFIG_PATH

    try:
        dados = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    tickers = dados.get("last_tickers") if isinstance(dados, dict) else None
    if not isinstance(tickers, list):
        return []
    return [t for t in tickers if isinstance(t, str) and t.strip()]


def _carregar_fundamentos(watchlist: list[str]) -> dict:
    """Lê a observação mais recente de cada ticker no histórico de fundamentos."""
    from flowscope.infrastructure.fii.fundamental_history_store import (
        JsonFundamentalHistoryStore,
    )

    store = JsonFundamentalHistoryStore()
    dados: dict = {}
    for ticker in watchlist:
        try:
            datas = store.datas(ticker)
        except Exception:
            datas = []
        if not datas:
            continue
        analise = store.obter(ticker, datas[-1])
        if analise is not None:
            dados[ticker.upper()] = analise
    return dados


def _rg_chaves(documentos: object) -> object:
    """Resolve, por ticker, as chaves dos RGs mensais avaliados no ledger."""
    from pathlib import Path

    from flowscope.application.documentos.catalogo import chave_documento

    metodo = getattr(documentos.guidance_service, "entradas_arvore", None)
    if not callable(metodo):
        return lambda _ticker: set()
    base = documentos.catalogo.base_dir

    def chaves(ticker: str) -> set:
        try:
            entradas = list(metodo(ticker))
        except Exception:
            return set()
        return {
            chave_documento(Path(entrada.caminho_pdf), base)
            for entrada in entradas
            if getattr(entrada, "caminho_pdf", None)
        }

    return chaves


def _guidance_paths(documentos: object, watchlist: list[str]) -> list:
    """Resolve os caminhos do ledger de guidance para a assinatura de estado."""
    try:
        return list(documentos.guidance_paths(watchlist))
    except Exception:
        return []


def iniciar_mcp() -> None:
    """Inicia o servidor MCP stdio a partir do cache local padrão."""
    from flowscope.presentation.navegacao import executar_servidor

    executar_servidor(montar_core_navegacao())


def _json_default(valor: object) -> str:
    """Serializa valores não nativos do JSON, como ``Decimal`` e ``date``."""
    if isinstance(valor, (Decimal, date)):
        return str(valor)
    raise TypeError(f"Objeto não serializável: {type(valor).__name__}")
