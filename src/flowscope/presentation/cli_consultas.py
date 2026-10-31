"""Subcomandos CLI de leitura para consulta e exportação de dados.

Espelha :mod:`flowscope.presentation.cli_acoes` para as operações de leitura:
``exportar`` materializa em arquivo dados calculados localmente (VWAP) e
``consultar`` busca dados remotos da B3 (proventos, fatos relevantes, notícias e
regulação) e imprime JSON. Cada subcomando declara apenas os parâmetros que lhe
são aplicáveis, eliminando a resolução por precedência entre flags conflitantes.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from flowscope.domain.structured import DocumentoProvento
from flowscope.presentation.cli import _json_default, _load_tickers, _parse_data


def adicionar_subcomandos_consulta(subcomandos: argparse._SubParsersAction) -> None:
    """Registra os subcomandos de leitura ``exportar`` e ``consultar``."""
    exportar = subcomandos.add_parser(
        "exportar", help="Exportar dados calculados localmente"
    )
    recursos_exportar = exportar.add_subparsers(dest="recurso")
    vwap = recursos_exportar.add_parser("vwap", help="Exportar o VWAP em CSV")
    vwap.add_argument(
        "--tickers",
        type=str,
        metavar="ARQUIVO",
        help="Arquivo texto com lista de tickers (um por linha)",
    )
    _opcao_saida(vwap)
    feriados = recursos_exportar.add_parser(
        "feriados", help="Exportar o calendário de feriados em CSV ou JSON"
    )
    feriados.add_argument(
        "--ano", type=int, required=True, metavar="AAAA",
        help="Ano do calendário",
    )
    feriados.add_argument(
        "--formato", choices=("csv", "json"), required=True,
        help="Formato de exportação",
    )
    _opcao_saida(feriados)

    consultar = subcomandos.add_parser(
        "consultar", help="Consultar dados remotos da B3"
    )
    recursos = consultar.add_subparsers(dest="recurso")
    proventos = recursos.add_parser(
        "proventos",
        parents=[_parser_datas(obrigatorias=True)],
        help="Extrair rendimentos e amortizações estruturados de um ticker",
    )
    proventos.add_argument("ticker", type=str, help="Ticker do ativo")
    _opcao_saida(proventos)

    fatos = recursos.add_parser(
        "fatos",
        parents=[_parser_datas(obrigatorias=False)],
        help="Extrair fatos relevantes, assembleias e avisos do ticker",
    )
    fatos.add_argument("ticker", type=str, help="Ticker do ativo")
    fatos.add_argument(
        "--categoria",
        type=str,
        metavar="CODIGO",
        help=(
            "Filtrar categoria de documento "
            "(1=Assembleias, 3=Aviso Acionistas, 4=Fatos Relevantes, "
            "48=Aviso Debenturistas, 107=Relatório Proventos)"
        ),
    )
    _opcao_saida(fatos)

    noticias = recursos.add_parser(
        "noticias",
        parents=[_parser_datas(obrigatorias=False)],
        help="Listar notícias do Plantão B3",
    )
    noticias.add_argument(
        "--palavra",
        type=str,
        metavar="TERMO",
        help="Filtrar notícias por palavra-chave no título",
    )
    _opcao_saida(noticias)

    regulacao = recursos.add_parser(
        "regulacao",
        help="Extrair censuras públicas e condições excepcionais da B3",
    )
    _opcao_saida(regulacao)
    feriados = recursos.add_parser(
        "feriados", help="Consultar o calendário local de feriados"
    )
    feriados.add_argument(
        "--ano", type=int, required=True, metavar="AAAA",
        help="Ano do calendário",
    )
    _opcao_saida(feriados)


def _parser_datas(*, obrigatorias: bool) -> argparse.ArgumentParser:
    """Constrói o parser pai ``add_help=False`` com as opções de período."""
    pai = argparse.ArgumentParser(add_help=False)
    pai.add_argument(
        "--data-inicio",
        type=_parse_data,
        metavar="AAAA-MM-DD",
        required=obrigatorias,
        help="Data de início da consulta",
    )
    pai.add_argument(
        "--data-fim",
        type=_parse_data,
        metavar="AAAA-MM-DD",
        required=obrigatorias,
        help="Data de fim da consulta",
    )
    return pai


def _opcao_saida(parser: argparse.ArgumentParser) -> None:
    """Adiciona a opção ``--saida`` (arquivo; padrão é ``stdout``)."""
    parser.add_argument(
        "--saida",
        type=str,
        metavar="ARQUIVO",
        help="Arquivo de saída (padrão: imprimir em stdout)",
    )


def executar_exportar(args: argparse.Namespace) -> None:
    """Executa um subcomando de exportação de dados calculados localmente."""
    if args.recurso == "vwap":
        _exportar_vwap(args)
    elif args.recurso == "feriados":
        _exportar_feriados(args)


def _exportar_vwap(args: argparse.Namespace) -> None:
    """Gera o CSV de VWAP e o grava no arquivo padrão ou indicado por ``--saida``."""
    from flowscope.application.use_cases import ExportVWAPUseCase
    from flowscope.infrastructure.b3.client import B3Client
    from flowscope.infrastructure.b3.repository import B3DataRepository
    from flowscope.infrastructure.calendar import build_calendar_services

    ticker_filter = _load_tickers(args.tickers) if args.tickers else None
    calendar = build_calendar_services()
    ref_date = date.fromisoformat(
        calendar.service.resolve_reference(date.today()).data_resolvida
    )
    repo = B3DataRepository(
        B3Client(business_day=calendar.lookup),
        business_day=calendar.lookup,
    )
    content = ExportVWAPUseCase(repo).execute(ref_date, ticker_filter=ticker_filter)

    saida = args.saida or f"vwap_{ref_date}.csv"
    Path(saida).write_text(content, encoding="utf-8")
    print(f"Arquivo exportado: {saida}")


def _exportar_feriados(args: argparse.Namespace) -> None:
    """Exporta o calendário de feriados sem criar arquivo sem ``--saida``."""
    from flowscope.infrastructure.calendar import build_calendar_services

    service = build_calendar_services().service
    conteudo = service.exportar_ano(args.ano, args.formato)
    if args.saida:
        Path(args.saida).write_text(conteudo, encoding="utf-8")
    else:
        print(conteudo, end="")


def consultar_feriados(args: argparse.Namespace) -> dict:
    """Consulta o calendário local de feriados, sem acessar a rede."""
    from flowscope.infrastructure.calendar import build_calendar_services

    payload = build_calendar_services().service.listar_ano(args.ano)
    _emitir_json(payload, args.saida)
    return payload


def executar_consultar(args: argparse.Namespace) -> None:
    """Despacha um subcomando de consulta a dados remotos da B3."""
    if args.recurso == "proventos":
        consultar_proventos(args)
    elif args.recurso == "fatos":
        consultar_fatos(args)
    elif args.recurso == "noticias":
        consultar_noticias(args)
    elif args.recurso == "feriados":
        consultar_feriados(args)
    else:
        consultar_regulacao(args)


def consultar_proventos(args: argparse.Namespace) -> list[DocumentoProvento]:
    """Extrai rendimentos e amortizações estruturados do ticker."""
    from flowscope.application.structured_use_cases import ExtrairProventosUseCase
    from flowscope.infrastructure.b3.funds_client import B3FundosClient
    from flowscope.infrastructure.b3.structured_repository import FundosRepository

    ticker = args.ticker.upper()
    repo = FundosRepository(B3FundosClient())
    documentos = ExtrairProventosUseCase(repo).execute(
        ticker,
        data_inicio=args.data_inicio,
        data_fim=args.data_fim,
        progress_callback=_progresso,
    )
    if not documentos and not args.saida:
        print(f"Nenhum dado disponível para {ticker}")
        return documentos
    _emitir_json([documento.to_dict() for documento in documentos], args.saida)
    if args.saida and documentos:
        print(f"Extração concluída: {len(documentos)} provento(s) em {args.saida}")
    return documentos


def consultar_fatos(args: argparse.Namespace) -> dict:
    """Extrai fatos relevantes do ticker via ``GetMaterialFacts``."""
    resultado = _caso_regulatorio().execute(
        "fatos",
        ticker=args.ticker.upper(),
        categoria=args.categoria,
        data_inicio=args.data_inicio,
        data_fim=args.data_fim,
    )
    _emitir_json(resultado, args.saida)
    return resultado


def consultar_noticias(args: argparse.Namespace) -> dict:
    """Lista as notícias do Plantão B3."""
    resultado = _caso_regulatorio().execute(
        "noticias",
        agencia="18",
        palavra=args.palavra,
        data_inicio=args.data_inicio,
        data_fim=args.data_fim,
    )
    _emitir_json(resultado, args.saida)
    return resultado


def consultar_regulacao(args: argparse.Namespace) -> dict:
    """Extrai censuras públicas e condições excepcionais da B3."""
    resultado = _caso_regulatorio().execute("regulacao")
    _emitir_json(resultado, args.saida)
    return resultado


def _caso_regulatorio() -> object:
    """Monta o caso de uso de extração regulatória a partir do cliente de fundos."""
    from flowscope.application.structured_use_cases import (
        ExtrairDadosRegulatoriosUseCase,
    )
    from flowscope.infrastructure.b3.funds_client import B3FundosClient

    return ExtrairDadosRegulatoriosUseCase(B3FundosClient())


def _emitir_json(dados: object, saida: str | None) -> None:
    """Grava o JSON em ``saida`` ou o imprime em ``stdout`` quando omitido."""
    texto = json.dumps(
        dados, indent=2, ensure_ascii=False, default=_json_default
    )
    if saida:
        Path(saida).write_text(texto, encoding="utf-8")
    else:
        print(texto)


def _progresso(mensagem: str, erro: bool) -> None:
    """Exibe o progresso da extração em stderr, sem poluir a saída JSON."""
    prefixo = "ERRO: " if erro else ""
    print(f"{prefixo}{mensagem}", file=sys.stderr)
