"""Testes do portão e da execução da avaliação de guidance de um documento."""

from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path

from flowscope.application.avaliar_guidance import AvaliarGuidanceUseCase
from flowscope.application.documentos.document_guidance import (
    GuidanceService,
    conteudo_arvore_guidance,
    rotulo_relatorio_gerencial,
)
from flowscope.application.resumo_documento import ResumoDocumento
from flowscope.domain.documents import DocumentoArquivo
from flowscope.domain.fii import METODO_IA, AvaliacaoGuidance, Guidance
from flowscope.domain.llm import LLMResposta

GUIDANCE = Guidance(
    valor_min=Decimal("0.74"),
    valor_max=Decimal("0.78"),
    periodo="restante do ano de 2026",
    data_relatorio=date(2026, 8, 1),
)


class _StoreFake:
    def __init__(self, inicial: dict | None = None) -> None:
        self._dados = dict(inicial or {})
        self.salvos: list[tuple] = []
        self.consultas: list[str] = []

    def obter(self, ticker):
        return next(
            (a.guidance for a in self._dados.values() if a.guidance is not None),
            None,
        )

    def obter_avaliacao(self, ticker, chave):
        return self._dados.get((ticker, chave))

    def avaliacoes(self, ticker):
        self.consultas.append(ticker)
        return {
            chave: avaliacao
            for (t, chave), avaliacao in self._dados.items()
            if t == ticker
        }

    def salvar_avaliacao(self, ticker, chave, avaliacao):
        self._dados[(ticker, chave)] = avaliacao
        self.salvos.append((ticker, chave, avaliacao))

    def caminho(self, ticker):
        return Path(f"/cache/guidance/{ticker}.json")


class _ExtratorFake:
    def __init__(self, resultado: Guidance | None = None) -> None:
        self.resultado = resultado
        self.chamadas: list[str] = []

    def __call__(self, texto, data_relatorio, caminho_pdf):
        self.chamadas.append(texto)
        return self.resultado


class _LLMFake:
    def __init__(self, resposta: str = "") -> None:
        self.resposta = resposta
        self.chamadas: list[str] = []

    def complete(self, messages, system_prompt=None):
        self.chamadas.append(messages[0]["content"])
        return LLMResposta(texto=self.resposta)


def _arquivo(
    categoria: str = "Relatorio",
    ano: int = 2026,
    mes: int = 8,
    short_summary: str | None = None,
    long_summary: str | None = None,
) -> DocumentoArquivo:
    return DocumentoArquivo(
        ticker="HGBS11",
        ano=ano,
        mes=mes,
        categoria=categoria,
        nome="10.pdf",
        tipo="pdf",
        caminho=Path("/cache/relatorio/10.pdf"),
        short_summary=short_summary,
        long_summary=long_summary,
    )


def _servico(store, extrator, **kwargs) -> GuidanceService:
    return GuidanceService(
        store, avaliador=AvaliarGuidanceUseCase(store, extrator), **kwargs
    )


class TestPrecisa:
    def test_outra_categoria_nao_dispara(self):
        servico = _servico(_StoreFake(), _ExtratorFake())
        assert servico.precisa(_arquivo(categoria="Assembleia")) is False

    def test_relatorio_dispara(self):
        servico = _servico(_StoreFake(), _ExtratorFake())
        assert servico.precisa(_arquivo()) is True

    def test_relatorio_antigo_ainda_dispara(self):
        servico = _servico(_StoreFake(), _ExtratorFake())
        assert servico.precisa(_arquivo(ano=2020, mes=1)) is True


class TestAvaliar:
    def test_sem_fontes_nao_avalia(self):
        store = _StoreFake()
        extrator = _ExtratorFake(GUIDANCE)
        servico = _servico(store, extrator)
        assert servico.avaliar(_arquivo(), None) is None
        assert servico.avaliar(_arquivo(), "   ") is None
        assert extrator.chamadas == []

    def test_cascata_usa_resumo_curto_primeiro(self):
        store = _StoreFake()
        extrator = _ExtratorFake(GUIDANCE)
        servico = _servico(store, extrator)
        resumo = ResumoDocumento("curto", "longo")
        resultado = servico.avaliar(_arquivo(), "texto integral", resumo)
        assert resultado.guidance == GUIDANCE
        assert extrator.chamadas == ["curto"]

    def test_usa_texto_quando_sem_resumo(self):
        store = _StoreFake()
        extrator = _ExtratorFake(GUIDANCE)
        servico = _servico(store, extrator)
        resultado = servico.avaliar(_arquivo(), "texto integral")
        assert resultado.guidance == GUIDANCE
        assert extrator.chamadas == ["texto integral"]

    def test_outra_categoria_nao_grava(self):
        store = _StoreFake()
        extrator = _ExtratorFake(GUIDANCE)
        servico = _servico(store, extrator)
        assert servico.avaliar(_arquivo(categoria="Comunicado"), "texto") is None
        assert store.salvos == []

    def test_chave_rg_injetada(self):
        store = _StoreFake()
        extrator = _ExtratorFake(GUIDANCE)
        servico = _servico(
            store, extrator, chave_rg=lambda arquivo: "hash-abc"
        )
        servico.avaliar(_arquivo(), "texto")
        assert store.salvos[0][1] == "hash-abc"

    def test_data_invalida_nao_avalia(self):
        store = _StoreFake()
        extrator = _ExtratorFake(GUIDANCE)
        servico = _servico(store, extrator)
        assert servico.avaliar(_arquivo(ano=0, mes=0), "texto") is None
        assert store.salvos == []


class TestPreferenciaIA:
    def test_ia_prevalece_em_servico_completo(self):
        store = _StoreFake()
        extrator = _ExtratorFake(GUIDANCE)
        llm = _LLMFake("GUIDANCE: SIM\nVALOR_MIN: 0,99\nVALOR_MAX: 0,99")
        servico = GuidanceService(
            store,
            extrator=extrator,
            llm_factory=lambda: llm,
            llm_available=lambda: True,
        )
        resultado = servico.avaliar(_arquivo(), "texto")
        assert resultado.metodo == METODO_IA
        assert resultado.guidance.valor_min == Decimal("0.99")
        assert extrator.chamadas == []

    def test_ia_indisponivel_usa_deterministico(self):
        store = _StoreFake()
        extrator = _ExtratorFake(GUIDANCE)
        llm = _LLMFake("GUIDANCE: SIM\nVALOR_MIN: 0,99")
        servico = GuidanceService(
            store,
            extrator=extrator,
            llm_factory=lambda: llm,
            llm_available=lambda: False,
        )
        resultado = servico.avaliar(_arquivo(), "texto")
        assert resultado.guidance == GUIDANCE
        assert extrator.chamadas == ["texto"]
        assert llm.chamadas == []


class TestRecuperacaoDeEntrada:
    def test_ja_avaliado_por_ia_nao_reavalia(self):
        existente = AvaliacaoGuidance(
            metodo=METODO_IA,
            data_relatorio=date(2026, 8, 1),
            guidance=GUIDANCE,
        )
        store = _StoreFake({("HGBS11", "10.pdf"): existente})
        extrator = _ExtratorFake(GUIDANCE)
        servico = _servico(store, extrator)
        assert servico.avaliar(_arquivo(), "texto") == existente
        assert store.salvos == []
        assert extrator.chamadas == []


def _servico_com_ia(
    store: _StoreFake, *, disponivel: bool = True
) -> GuidanceService:
    return GuidanceService(
        store,
        extrator=_ExtratorFake(GUIDANCE),
        llm_factory=lambda: _LLMFake(),
        llm_available=lambda: disponivel,
    )


class TestPendentesGuidance:
    def test_ia_disponivel_reflete_a_estrategia(self):
        assert _servico_com_ia(_StoreFake()).ia_disponivel() is True
        assert (
            _servico_com_ia(_StoreFake(), disponivel=False).ia_disponivel()
            is False
        )

    def test_entrada_ausente_e_pendente_com_ia(self):
        servico = _servico_com_ia(_StoreFake())
        assert servico.pendente(_arquivo()) is True

    def test_entrada_ia_nao_e_pendente(self):
        existente = AvaliacaoGuidance(
            metodo=METODO_IA,
            data_relatorio=date(2026, 8, 1),
            guidance=GUIDANCE,
        )
        store = _StoreFake({("HGBS11", "10.pdf"): existente})
        assert _servico_com_ia(store).pendente(_arquivo()) is False

    def test_entrada_deterministica_e_pendente_com_ia(self):
        existente = AvaliacaoGuidance(
            metodo="deterministico",
            data_relatorio=date(2026, 8, 1),
            guidance=GUIDANCE,
        )
        store = _StoreFake({("HGBS11", "10.pdf"): existente})
        assert _servico_com_ia(store).pendente(_arquivo()) is True

    def test_sem_ia_nada_e_pendente(self):
        servico = _servico_com_ia(_StoreFake(), disponivel=False)
        assert servico.pendente(_arquivo()) is False
        assert servico.pendentes([_arquivo()]) == []

    def test_outra_categoria_nao_e_pendente(self):
        servico = _servico_com_ia(_StoreFake())
        assert servico.pendente(_arquivo(categoria="Comunicado")) is False

    def test_data_invalida_nao_e_pendente(self):
        servico = _servico_com_ia(_StoreFake())
        assert servico.pendente(_arquivo(ano=0, mes=0)) is False

    def test_pendentes_le_o_ledger_uma_vez_por_ticker(self):
        store = _StoreFake()
        servico = _servico_com_ia(store)
        primeiro = _arquivo()
        segundo = replace(
            primeiro,
            nome="20.pdf",
            caminho=Path("/cache/relatorio/20.pdf"),
        )
        pendentes = servico.pendentes([primeiro, segundo])
        assert pendentes == [primeiro, segundo]
        assert store.consultas == ["HGBS11"]


class TestEntradasArvore:
    def _avaliacao(self, guidance=GUIDANCE, caminho: str | None = None):
        return AvaliacaoGuidance(
            metodo=METODO_IA,
            data_relatorio=date(2026, 8, 1),
            caminho_pdf=caminho,
            guidance=guidance,
        )

    def test_disponibiliza_entradas_com_valor(self):
        store = _StoreFake(
            {
                ("HGBS11", "chave-1"): self._avaliacao(
                    caminho="/cache/relatorio/10.pdf"
                ),
            }
        )
        servico = _servico(store, _ExtratorFake(GUIDANCE))
        entradas = servico.entradas_arvore("HGBS11")
        assert len(entradas) == 1
        entrada = entradas[0]
        assert (entrada.ano, entrada.mes) == (2026, 8)
        assert entrada.caminho_pdf == "/cache/relatorio/10.pdf"
        assert entrada.chave == "chave-1"
        assert entrada.guidance == GUIDANCE

    def test_exclui_ausencias(self):
        store = _StoreFake(
            {
                ("HGBS11", "com-guidance"): self._avaliacao(),
                ("HGBS11", "ausente"): AvaliacaoGuidance(
                    metodo=METODO_IA,
                    data_relatorio=date(2026, 7, 1),
                    guidance=None,
                ),
            }
        )
        servico = _servico(store, _ExtratorFake(GUIDANCE))
        entradas = servico.entradas_arvore("HGBS11")
        assert [e.chave for e in entradas] == ["com-guidance"]

    def test_nao_altera_o_ledger(self):
        store = _StoreFake(
            {("HGBS11", "chave-1"): self._avaliacao()},
        )
        servico = _servico(store, _ExtratorFake(GUIDANCE))
        servico.entradas_arvore("HGBS11")
        assert store.salvos == []

    def test_estado_arvore_le_o_ledger_uma_vez(self):
        store = _StoreFake(
            {("HGBS11", "10.pdf"): self._avaliacao()},
        )
        servico = _servico_com_ia(store)
        pendentes, entradas = servico.estado_arvore("HGBS11", [_arquivo()])
        assert store.consultas == ["HGBS11"]
        assert len(entradas) == 1
        assert pendentes == []


class TestRotuloRelatorioGerencial:
    def test_usa_nome_do_documento_do_catalogo(self, tmp_path):
        caminho = tmp_path / "10.pdf"
        documento = _arquivo()
        documento = replace(documento, caminho=caminho)
        rotulo = rotulo_relatorio_gerencial(
            date(2026, 8, 1), str(caminho), {caminho: documento}
        )
        assert rotulo == "Relatório Gerencial — ago/26 (10.pdf)"

    def test_fallback_para_basename_do_caminho(self):
        rotulo = rotulo_relatorio_gerencial(date(2026, 8, 1), "/cache/relatorio/x.pdf")
        assert rotulo == "Relatório Gerencial — ago/26 (x.pdf)"

    def test_sem_caminho_usa_vazio(self):
        assert rotulo_relatorio_gerencial(date(2026, 8, 1), None).endswith("()")

    def test_conteudo_arvore_composto(self, tmp_path):
        caminho = tmp_path / "10.pdf"
        store = _StoreFake(
            {
                ("HGBS11", "chave-1"): AvaliacaoGuidance(
                    metodo=METODO_IA,
                    data_relatorio=date(2026, 8, 1),
                    caminho_pdf=str(caminho),
                    guidance=GUIDANCE,
                )
            }
        )
        servico = _servico(store, _ExtratorFake(GUIDANCE))
        entrada = servico.entradas_arvore("HGBS11")[0]
        documento = replace(_arquivo(), caminho=caminho)
        conteudo = conteudo_arvore_guidance(entrada, {caminho: documento})
        assert conteudo.startswith(entrada.texto)
        assert conteudo.endswith("Relatório Gerencial — ago/26 (10.pdf)")
