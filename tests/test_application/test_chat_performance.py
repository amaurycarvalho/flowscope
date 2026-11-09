"""Testes do ramo ``/performance`` da árvore de conhecimento."""

from flowscope.application.chat.performance import (
    AVISO_EVENTO_SUSPEITO,
    ORIENTACAO_SEM_RESULTADOS,
    FontePerformance,
)


def _snapshot(**mudancas) -> dict:
    dados = {
        "schema_version": 1,
        "source": "headless",
        "ref_date": "2026-11-07",
        "period_days": 30,
        "sampling_method": "fibonacci",
        "cached_at": "2026-11-07T18:30:00+00:00",
        "benchmarks": ["IFIX"],
        "default": "IFIX",
        "ticker_types": {"HGLG11": "FII"},
        "results": {
            "IFIX": {
                "benchmark": "IFIX",
                "index_available": True,
                "return_basis": "total",
                "tickers": [
                    {
                        "ticker": "HGLG11",
                        "ticker_return": 0.12,
                        "index_return": 0.05,
                        "excess_pp": 7.0,
                        "observations": 20,
                        "suspicious_event": False,
                    }
                ],
            }
        },
    }
    dados.update(mudancas)
    return dados


def _arvore(snapshot):
    from flowscope.application.chat.arvore import ArvoreConhecimento

    raiz = FontePerformance(snapshot).construir()
    return ArvoreConhecimento(raiz) if raiz is not None else None


class TestFontePerformance:
    def test_ramo_com_configuracao_e_benchmarks(self):
        arvore = _arvore(_snapshot())
        assert arvore.existe("/performance")
        assert arvore.existe("/performance/configuracao")
        assert arvore.existe("/performance/benchmarks")
        assert arvore.existe("/performance/benchmarks/IFIX/resumo")
        assert arvore.existe(
            "/performance/benchmarks/IFIX/tickers/HGLG11"
        )

    def test_configuracao_expoe_contexto(self):
        arvore = _arvore(_snapshot())
        texto = arvore.obter("/performance/configuracao")
        assert "data_referencia: 2026-11-07" in texto
        assert "periodo_dias: 30" in texto
        assert "amostragem: fibonacci" in texto
        assert "calculado_em:" in texto
        assert "IFIX=total" in texto

    def test_resumo_informa_indice_base_e_tickers(self):
        arvore = _arvore(_snapshot())
        texto = arvore.obter("/performance/benchmarks/IFIX/resumo")
        assert "indice_disponivel: sim" in texto
        assert "base_retorno: total" in texto
        assert "tickers_elegiveis: 1" in texto
        assert "HGLG11" in texto

    def test_ticker_expoe_retornos_e_observacoes(self):
        arvore = _arvore(_snapshot())
        texto = arvore.obter("/performance/benchmarks/IFIX/tickers/HGLG11")
        assert "retorno_ticker: 0.12" in texto
        assert "retorno_indice: 0.05" in texto
        assert "excesso_pp: 7.0" in texto
        assert "observacoes: 20" in texto
        assert AVISO_EVENTO_SUSPEITO not in texto

    def test_evento_suspeito_aparece(self):
        snapshot = _snapshot()
        snapshot["results"]["IFIX"]["tickers"][0]["suspicious_event"] = True
        arvore = _arvore(snapshot)
        texto = arvore.obter("/performance/benchmarks/IFIX/tickers/HGLG11")
        assert AVISO_EVENTO_SUSPEITO in texto

    def test_sem_snapshot_omite_ramo(self):
        assert FontePerformance(None).construir() is None
        assert _arvore(None) is None

    def test_snapshot_sem_resultados_expoe_orientacao(self):
        arvore = _arvore(_snapshot(benchmarks=[], results={}))
        assert arvore.existe("/performance/configuracao")
        assert arvore.existe("/performance/orientacao")
        assert not arvore.existe("/performance/benchmarks")
        assert arvore.obter("/performance/orientacao") == ORIENTACAO_SEM_RESULTADOS

    def test_benchmark_com_indice_indisponivel(self):
        snapshot = _snapshot()
        snapshot["results"]["IFIX"]["index_available"] = False
        texto = _arvore(snapshot).obter("/performance/benchmarks/IFIX/resumo")
        assert "indice_disponivel: nao" in texto
