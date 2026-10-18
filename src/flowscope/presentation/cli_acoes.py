"""Subcomandos CLI de ação para agendamento externo.

Expõe as ações de atualização do FlowScope (carregar watchlist, atualizar
fundamentos/documentos/notícias e resumir pendentes) como subcomandos headless.
Cada subcomando de escrita adquire o lock global de ação (``--esperar <s>``,
com erro estruturado ``operacao_em_andamento``), imprime JSON em ``stdout`` e
manda o diagnóstico para ``stderr``.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date
from pathlib import Path

from flowscope.application.fundamental_analysis import FundamentalAnalysisUseCase
from flowscope.domain.sampling import SamplingConfig
from flowscope.infrastructure.action_lock import ActionLock, OperacaoEmAndamento
from flowscope.infrastructure.b3.documentos_aquisicao import AquisicaoDocumentos
from flowscope.infrastructure.b3.noticias_carga import AquisicaoNoticias
from flowscope.infrastructure.fii.b3_price import B3MarketPriceFromResult
from flowscope.infrastructure.referencia import gravar_config
from flowscope.presentation.cli_resumos import (
    AcaoError,
    last_tickers,
    progresso_stderr,
    resumir_documentos,
    resumir_noticias,
)

logger = logging.getLogger("flowscope")


def carregar_watchlist(arquivo: str) -> dict:
    """Lê, valida e persiste a watchlist de um arquivo."""
    caminho = Path(arquivo)
    if not caminho.is_file():
        raise AcaoError("arquivo_inexistente", str(caminho))
    try:
        conteudo = caminho.read_text(encoding="utf-8")
    except OSError as exc:
        raise AcaoError("arquivo_ilegivel", str(exc)) from exc
    tickers = [linha.strip().upper() for linha in conteudo.splitlines() if linha.strip()]
    if not tickers:
        raise AcaoError("watchlist_vazia", str(caminho))
    gravar_config(
        {"last_tickers": tickers, "last_ticker_file": str(caminho.resolve())}
    )
    return {"tickers": tickers, "arquivo": str(caminho.resolve())}


def _montar_caso_fundamental(
    nucleo: object, mercado: object | None
) -> FundamentalAnalysisUseCase:
    """Monta o caso de uso da análise fundamentalista a partir do núcleo."""
    return FundamentalAnalysisUseCase(
        repository=nucleo.fundamental_repo,
        mercado=mercado,
        fundamental_provider=nucleo.fundamental_provider,
        ffo_provider=nucleo.fundamental_ffo_provider,
        historico_dividendos=nucleo.fundamental_dividend_provider,
        acionistas_provider=nucleo.fundamental_acionistas_provider,
        free_float_provider=nucleo.fundamental_acionistas_provider,
        short_interest_provider=nucleo.fundamental_short_interest_provider,
        indexadores_provider=nucleo.fundamental_indexadores_provider,
        historico_store=nucleo.history_store,
        resolver_fiagro=nucleo.resolver_fiagro,
        bdr_provider=nucleo.fundamental_bdr_provider,
        guidance_store=nucleo.guidance_store,
    )


def atualizar_fundamentos(data: date, nucleo: object | None = None) -> dict:
    """Atualiza os fundamentos da watchlist para a data informada.

    A data é a de hoje quando ``--data`` não for passado. Roda a análise de
    mercado antes da análise fundamentalista para preservar Preço Típico e
    fallbacks, grava o histórico e registra o marcador da última carga.
    """
    from flowscope.presentation.composicao import (
        montar_nucleo,
        registrar_carga_fundamentos,
    )

    nucleo = nucleo or montar_nucleo()
    watchlist = last_tickers()
    if not watchlist:
        raise AcaoError("watchlist_ausente", "last_tickers vazio ou ausente")
    progresso_stderr(f"Análise de mercado para {data.isoformat()}...")
    resultado = nucleo.analyze.execute(data, watchlist, config=SamplingConfig())
    daily = {
        ticker: dados.get("daily_data", [])
        for ticker, dados in resultado.items()
        if isinstance(dados, dict)
    }
    mercado = B3MarketPriceFromResult(daily)
    caso = _montar_caso_fundamental(nucleo, mercado)
    progresso_stderr("Análise fundamentalista...")
    analises = caso.execute(watchlist, data, force_refresh=True)
    registrar_carga_fundamentos(data)
    return {
        "data": data.isoformat(),
        "tickers": watchlist,
        "processados": len(analises),
    }


def _desfecho_documentos(resultado: object) -> str:
    """Classifica o desfecho da aquisição de um ticker."""
    falhas = getattr(resultado, "falhas", 0)
    if falhas:
        return "falha"
    if getattr(resultado, "adquiridos", 0) == 0:
        return "nada_novo"
    return "atualizado"


def atualizar_documentos(data: date, ticker: str | None = None) -> dict:
    """Adquire os documentos da data para um ticker ou para a watchlist inteira."""
    from flowscope.presentation.composicao import montar_nucleo

    nucleo = montar_nucleo()
    watchlist = last_tickers()
    alvos = _resolver_alvos(watchlist, ticker)
    resultados = _adquirir_por_ticker(nucleo, alvos, data)
    resposta: dict = {"data": data.isoformat(), "resultados": resultados}
    if any(desfecho == "falha" for desfecho in resultados.values()):
        resposta["falha"] = True
    return resposta


def _resolver_alvos(watchlist: list[str], ticker: str | None) -> list[str]:
    """Resolve os tickers alvo, validando contra a watchlist."""
    if ticker:
        normalizado = ticker.strip().upper()
        if normalizado not in watchlist:
            raise AcaoError("ticker_fora_watchlist", normalizado)
        return [normalizado]
    if not watchlist:
        raise AcaoError("watchlist_ausente", "last_tickers vazio ou ausente")
    return list(watchlist)


def _adquirir_por_ticker(
    nucleo: object, alvos: list[str], data: date
) -> dict[str, str]:
    """Adquire e deduplica os documentos de cada ticker, por desfecho."""
    resultados: dict[str, str] = {}
    for ticker in alvos:
        progresso_stderr(f"Documentos de {ticker}...")
        try:
            aquisicao: AquisicaoDocumentos = nucleo.aquisicao_documentos
            desfecho = aquisicao.adquirir(ticker, data)
            nucleo.deduplicar_documentos(ticker, None)
            resultados[ticker] = _desfecho_documentos(desfecho)
        except Exception:  # falha de um ticker não aborta o lote
            logger.warning("Falha ao adquirir documentos de %s", ticker, exc_info=True)
            resultados[ticker] = "falha"
    return resultados


def atualizar_noticias(data: date) -> dict:
    """Executa a aquisição incremental das notícias do Plantão B3."""
    from flowscope.presentation.composicao import montar_nucleo

    nucleo = montar_nucleo()
    progresso_stderr(f"Notícias para {data.isoformat()}...")
    aquisicao: AquisicaoNoticias = nucleo.aquisicao_noticias
    adquiridos = aquisicao.adquirir(data)
    nucleo.deduplicar_noticias(None)
    return {"data": data.isoformat(), "adquiridos": adquiridos or 0}


def adicionar_subcomandos_acao(subcomandos: argparse._SubParsersAction) -> None:
    """Registra os subcomandos de ação ``carregar``, ``atualizar`` e ``resumir``."""
    carregar = subcomandos.add_parser("carregar", help="Carregar dados externos")
    recursos_carregar = carregar.add_subparsers(dest="recurso")
    watchlist = recursos_carregar.add_parser("watchlist", help="Carregar a watchlist")
    watchlist.add_argument("arquivo", type=str, help="Arquivo com um ticker por linha")
    _opcoes_saida(watchlist)

    atualizar = subcomandos.add_parser("atualizar", help="Atualizar caches")
    recursos_atualizar = atualizar.add_subparsers(dest="recurso")
    fundamentos = recursos_atualizar.add_parser("fundamentos", help="Atualizar fundamentos")
    _opcao_data(fundamentos)
    _opcoes_saida(fundamentos)
    documentos = recursos_atualizar.add_parser("documentos", help="Atualizar documentos")
    documentos.add_argument("ticker", nargs="?", default=None, help="Ticker opcional")
    _opcao_data(documentos)
    _opcoes_saida(documentos)
    noticias = recursos_atualizar.add_parser("noticias", help="Atualizar notícias")
    _opcao_data(noticias)
    _opcoes_saida(noticias)

    resumir = subcomandos.add_parser("resumir", help="Resumir pendentes")
    recursos_resumir = resumir.add_subparsers(dest="recurso")
    resumir_docs = recursos_resumir.add_parser("documentos", help="Resumir documentos")
    resumir_docs.add_argument(
        "ticker",
        nargs="?",
        default=None,
        help="Ticker da watchlist (omitido processa toda a watchlist)",
    )
    _opcoes_saida(resumir_docs)
    resumir_not = recursos_resumir.add_parser("noticias", help="Resumir notícias")
    _opcoes_saida(resumir_not)


def _opcao_data(parser: argparse.ArgumentParser) -> None:
    """Adiciona a opção ``--data``, cujo padrão é a data de hoje."""
    parser.add_argument(
        "--data",
        type=_parse_data,
        metavar="AAAA-MM-DD",
        help="Data de referência (padrão: hoje)",
    )


def _opcoes_saida(parser: argparse.ArgumentParser) -> None:
    """Adiciona as opções comuns de saída e espera do lock."""
    parser.add_argument(
        "--pretty", action="store_true", help="Formatar a saída JSON para leitura"
    )
    parser.add_argument(
        "--esperar",
        type=float,
        default=0.0,
        metavar="S",
        help="Segundos a esperar pelo lock global antes de falhar",
    )


def _parse_data(valor: str) -> date:
    """Interpreta uma data no formato ``AAAA-MM-DD``."""
    try:
        return date.fromisoformat(valor)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Data inválida: {valor!r} (use o formato AAAA-MM-DD)"
        ) from None


def _data_efetiva(valor: date | None) -> date:
    """Resolve a data do subcomando: ``--data`` ou a data local de hoje."""
    if valor is not None:
        return valor
    return date.today()


def _despachar_acao(args: argparse.Namespace) -> dict:
    """Executa o subcomando de ação e devolve o resultado estruturado."""
    if args.comando == "carregar":
        return carregar_watchlist(args.arquivo)
    if args.comando == "atualizar":
        return _despachar_atualizar(args)
    return _despachar_resumir(args)


def _despachar_atualizar(args: argparse.Namespace) -> dict:
    """Executa os subcomandos ``atualizar``."""
    if args.recurso == "fundamentos":
        return atualizar_fundamentos(_data_efetiva(args.data))
    if args.recurso == "documentos":
        return atualizar_documentos(_data_efetiva(args.data), args.ticker)
    return atualizar_noticias(_data_efetiva(args.data))


def _despachar_resumir(args: argparse.Namespace) -> dict:
    """Executa os subcomandos ``resumir``."""
    if args.recurso == "documentos":
        return resumir_documentos(args.ticker)
    return resumir_noticias()


def executar_acao(args: argparse.Namespace) -> None:
    """Executa um subcomando de ação, com lock, saída JSON e código de saída.

    Erros de domínio e a indisponibilidade do lock são impressos como JSON
    estruturado em ``stdout``; o diagnóstico vai para ``stderr`` e o processo
    encerra com código 1.
    """
    pretty = bool(getattr(args, "pretty", False))
    esperar = float(getattr(args, "esperar", 0.0) or 0.0)
    try:
        with ActionLock().adquirir(esperar):
            dados = _despachar_acao(args)
    except OperacaoEmAndamento:
        _imprimir_erro(
            "operacao_em_andamento",
            "outra operação de escrita já está em andamento",
            pretty,
        )
        sys.exit(1)
    except AcaoError as exc:
        _imprimir_erro(exc.motivo, exc.detalhe, pretty)
        sys.exit(1)
    _imprimir_json(dados, pretty)
    if dados.get("falha"):
        sys.exit(1)


def _imprimir_erro(motivo: str, detalhe: str, pretty: bool) -> None:
    """Imprime um erro estruturado em ``stdout`` e o diagnóstico em ``stderr``."""
    _imprimir_json({"erro": {"motivo": motivo, "detalhe": detalhe}}, pretty)
    print(f"Erro ({motivo}): {detalhe}", file=sys.stderr)


def _imprimir_json(dados: object, pretty: bool) -> None:
    """Imprime o resultado como JSON em ``stdout``."""
    from flowscope.presentation.cli import _json_default

    print(
        json.dumps(
            dados,
            indent=2 if pretty else None,
            ensure_ascii=False,
            default=_json_default,
        )
    )
