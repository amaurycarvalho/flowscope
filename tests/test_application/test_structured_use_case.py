from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from flowscope.application.structured_use_cases import ExtrairProventosUseCase
from flowscope.domain.structured import (
    CNPJ,
    DocumentoProvento,
    Entidade,
    ISIN,
    Provento,
    ValorProvento,
)

_ENTIDADE = Entidade(
    nome="ALIANZA TRUST RENDA IMOBILIÁRIA - FII",
    cnpj=CNPJ("28.737.771/0001-85"),
    nome_administrador="BTG PACTUAL SERVIÇOS FINANCEIROS S/A DTVM",
    cnpj_administrador=CNPJ("59.281.253/0001-23"),
    responsavel="Leandro Pereira",
    telefone="(11) 3383-3102",
)

_PROVENTO = Provento(
    codigo_isin=ISIN("BRALZRCTF006"),
    codigo_negociacao="ALZR11",
    tipo="Rendimento",
    data_base=date(2026, 6, 18),
    valor_por_unidade=ValorProvento(Decimal("0.08355")),
    data_pagamento=date(2026, 6, 25),
    periodo_referencia="Maio-2026",
    isento_ir=True,
)


def _documento(id_documento: str = "1224160") -> DocumentoProvento:
    return DocumentoProvento(
        ticker="ALZR11",
        id_fnet="20294",
        id_documento=id_documento,
        url_documento=f"https://fnet.bmfbovespa.com.br/fnet/publico/exibirDocumento?id={id_documento}",
        data_extracao="2026-07-29T14:30:00-03:00",
        entidade=_ENTIDADE,
        provento=_PROVENTO,
    )


@pytest.fixture
def mock_proventos_repository():
    return MagicMock()


class TestExtrairProventosUseCase:
    def test_sucesso(self, mock_proventos_repository):
        mock_proventos_repository.resolver_ticker.return_value = "20294"
        mock_proventos_repository.listar_documentos.return_value = [
            {"id": "1224160", "urlViewerFundosNet": "https://exemplo?id=1224160"},
            {"id": "1224161", "urlViewerFundosNet": "https://exemplo?id=1224161"},
        ]
        mock_proventos_repository.extrair_detalhes.side_effect = [
            _documento("1224160"),
            _documento("1224161"),
        ]
        use_case = ExtrairProventosUseCase(mock_proventos_repository)
        resultado = use_case.execute(
            "ALZR11",
            data_inicio=date(2026, 1, 1),
            data_fim=date(2026, 7, 29),
        )
        assert len(resultado) == 2
        assert resultado[0].ticker == "ALZR11"
        mock_proventos_repository.listar_documentos.assert_called_once_with(
            "20294", date(2026, 1, 1), date(2026, 7, 29), 41
        )

    def test_ticker_sem_resolucao_retorna_vazio(self, mock_proventos_repository):
        mock_proventos_repository.resolver_ticker.return_value = None
        use_case = ExtrairProventosUseCase(mock_proventos_repository)
        resultado = use_case.execute(
            "PETR4",
            data_inicio=date(2026, 1, 1),
            data_fim=date(2026, 7, 29),
        )
        assert resultado == []
        mock_proventos_repository.listar_documentos.assert_not_called()
        mock_proventos_repository.extrair_detalhes.assert_not_called()

    def test_periodo_sem_documentos_retorna_vazio(self, mock_proventos_repository):
        mock_proventos_repository.resolver_ticker.return_value = "20294"
        mock_proventos_repository.listar_documentos.return_value = []
        use_case = ExtrairProventosUseCase(mock_proventos_repository)
        resultado = use_case.execute(
            "ALZR11",
            data_inicio=date(2026, 1, 1),
            data_fim=date(2026, 7, 29),
        )
        assert resultado == []

    def test_erro_em_documento_loga_e_continua(self, mock_proventos_repository):
        mock_proventos_repository.resolver_ticker.return_value = "20294"
        mock_proventos_repository.listar_documentos.return_value = [
            {"id": "1224160", "urlViewerFundosNet": "https://exemplo?id=1224160"},
            {"id": "1224161", "urlViewerFundosNet": "https://exemplo?id=1224161"},
        ]
        mock_proventos_repository.extrair_detalhes.side_effect = [
            RuntimeError("HTML inacessível"),
            _documento("1224161"),
        ]
        use_case = ExtrairProventosUseCase(mock_proventos_repository)
        resultado = use_case.execute(
            "ALZR11",
            data_inicio=date(2026, 1, 1),
            data_fim=date(2026, 7, 29),
        )
        assert len(resultado) == 1
        assert resultado[0].id_documento == "1224161"

    def test_progress_callback_invocado_em_cada_etapa(self, mock_proventos_repository):
        mock_proventos_repository.resolver_ticker.return_value = "20294"
        mock_proventos_repository.listar_documentos.return_value = [
            {"id": "1224160", "urlViewerFundosNet": "https://exemplo?id=1224160"},
        ]
        mock_proventos_repository.extrair_detalhes.return_value = _documento()
        callback = MagicMock()
        use_case = ExtrairProventosUseCase(mock_proventos_repository)
        use_case.execute(
            "ALZR11",
            data_inicio=date(2026, 1, 1),
            data_fim=date(2026, 7, 29),
            progress_callback=callback,
        )
        mensagens = [call.args[0] for call in callback.call_args_list]
        erros = [call.args[1] for call in callback.call_args_list]
        assert "Resolvendo ticker ALZR11" in mensagens
        assert "Listando documentos de ALZR11" in mensagens
        assert any("Extraindo documento" in m for m in mensagens)
        assert all(erro is False for erro in erros)
