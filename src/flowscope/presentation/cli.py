"""Interface de linha de comando do FlowScope."""

import argparse
import json
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    """Constrói o parser de argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        prog="flowscope",
        allow_abbrev=False,
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
        "--version",
        action="store_true",
        help="Exibir versão",
    )
    parser.add_argument(
        "--create-shortcut",
        action="store_true",
        help="Criar atalho no desktop (Linux)",
    )
    subcomandos = parser.add_subparsers(dest="comando")
    _adicionar_subcomandos_nav(subcomandos)
    _adicionar_subcomando_mcp(subcomandos)
    from flowscope.presentation.cli_acoes import adicionar_subcomandos_acao
    from flowscope.presentation.cli_consultas import adicionar_subcomandos_consulta

    adicionar_subcomandos_acao(subcomandos)
    adicionar_subcomandos_consulta(subcomandos)
    return parser


def _adicionar_subcomando_mcp(subcomandos: argparse._SubParsersAction) -> None:
    """Registra o subcomando ``mcp`` com a preparação opcional na inicialização."""
    mcp = subcomandos.add_parser(
        "mcp", help="Iniciar o servidor MCP (stdio), com preparação opcional"
    )
    mcp.add_argument(
        "--watchlist", type=str, metavar="ARQUIVO", help="Watchlist a carregar"
    )
    mcp.add_argument(
        "--data", type=_parse_data, metavar="AAAA-MM-DD", help="Data de referência"
    )


def _adicionar_subcomandos_nav(subcomandos: argparse._SubParsersAction) -> None:
    """Registra o subcomando ``nav`` com as operações de navegação."""
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
    data_referencia = operacoes.add_parser(
        "data-referencia", help="Ler a data de referência resolvida"
    )
    data_referencia.add_argument(
        "--pretty", action="store_true", help="Formatar a saída JSON para leitura humana"
    )
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
    if operacao == "data-referencia":
        return "data_referencia"
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


def montar_core_navegacao(reference_date: date | None = None) -> object:
    """Ponto de composição headless da navegação sobre o cache local padrão.

    Monta a mesma árvore de conhecimento do chat a partir do cache local —
    conhecimento do FlowScope, fundamentos, documentos, notícias, guidance e
    direitos/obrigações — e a embrulha no ``NavegacaoCore`` reusado pela CLI e
    pelo servidor MCP. Cada ticker é carregado na data de referência resolvida
    ``R`` (override por ``reference_date``): observação exata de ``R``, senão a
    mais recente anterior ou igual; sem ``R``, a mais recente.
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
    from flowscope.presentation.composicao import (
        montar_nucleo,
        resolver_data_referencia,
    )
    from flowscope.presentation.gui.app_tabs import TAB_CONTENT
    from flowscope.presentation.gui.widgets.about_panel import (
        APRESENTACAO,
        LICENCA,
        REPOSITORIO_URL,
    )

    nucleo = montar_nucleo()
    documentos = nucleo.documentos
    noticias = nucleo.noticias
    watchlist = _watchlist_config()
    referencia = reference_date or resolver_data_referencia()
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
        FonteFundamentos(
            _carregar_fundamentos(watchlist, referencia),
            watchlist=watchlist,
            data_referencia=referencia,
        ),
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


def _carregar_fundamentos(
    watchlist: list[str], reference_date: date | None = None
) -> dict:
    """Lê a observação de cada ticker na data de referência resolvida.

    Com ``reference_date`` informado, usa a observação exata dessa data ou, na
    ausência, a mais recente anterior ou igual. Sem ``reference_date``, usa a
    observação mais recente de cada ticker.
    """
    from flowscope.infrastructure.fii.fundamental_history_store import (
        JsonFundamentalHistoryStore,
    )

    store = JsonFundamentalHistoryStore()
    dados: dict = {}
    for ticker in watchlist:
        try:
            if reference_date is not None:
                analise = store.obter_em_ou_antes(ticker, reference_date)
            else:
                datas = store.datas(ticker)
                analise = store.obter(ticker, datas[-1]) if datas else None
        except Exception:
            analise = None
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


def iniciar_mcp(
    watchlist: str | None = None, data: date | None = None
) -> None:
    """Inicia o servidor MCP stdio a partir do cache local padrão.

    Com ``watchlist`` e/ou ``data``, executa antes as etapas de ``carregar
    watchlist`` e ``atualizar fundamentos`` sob o lock global (liberado antes de
    servir). A árvore é montada refletindo a data de referência resolvida.
    """
    from flowscope.presentation.navegacao import executar_servidor

    if watchlist or data:
        _preparar_mcp(watchlist, data)
    executar_servidor(montar_core_navegacao(reference_date=data))


def _preparar_mcp(watchlist: str | None, data: date | None) -> None:
    """Executa a preparação opcional do servidor MCP, abortando em falha."""
    from flowscope.infrastructure.action_lock import ActionLock, OperacaoEmAndamento
    from flowscope.presentation import cli_acoes

    try:
        with ActionLock().adquirir(0.0):
            if watchlist:
                cli_acoes.carregar_watchlist(watchlist)
            if data:
                cli_acoes.atualizar_fundamentos(data)
    except OperacaoEmAndamento:
        _abortar_mcp("operacao_em_andamento", "outra operação de escrita em andamento")
    except cli_acoes.AcaoError as exc:
        _abortar_mcp(exc.motivo, exc.detalhe)


def _abortar_mcp(motivo: str, detalhe: str) -> None:
    """Aborta a inicialização do MCP com código 1, sem iniciar o servidor."""
    print(f"Falha na preparação do MCP ({motivo}): {detalhe}", file=sys.stderr)
    sys.exit(1)


def _json_default(valor: object) -> str:
    """Serializa valores não nativos do JSON, como ``Decimal`` e ``date``."""
    if isinstance(valor, (Decimal, date)):
        return str(valor)
    raise TypeError(f"Objeto não serializável: {type(valor).__name__}")
