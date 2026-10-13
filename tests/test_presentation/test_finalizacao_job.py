"""Testes headless do trabalho de finalização definitiva de extração."""

from pathlib import Path

from flowscope.application.document_preview import StatusExtracao
from flowscope.application.finalizacao_extracao import ItemPendente
from flowscope.application.resumo_documento import ResumoDocumento
from flowscope.domain.documents import DocumentoArquivo
from flowscope.presentation.gui.background.context import JobContext
from flowscope.presentation.gui.background.events import Erro, Progresso
from flowscope.presentation.gui.background.job import JobHandle, Politica
from flowscope.presentation.gui.finalizacao_job import executar_finalizacao


def _arquivo(nome: str) -> DocumentoArquivo:
    return DocumentoArquivo(
        ticker="ALZR11",
        ano=2026,
        mes=2,
        categoria="Relatorio",
        nome=nome,
        tipo="pdf",
        caminho=Path("/tmp") / nome,
    )


def _item(status: StatusExtracao, nome: str = "10.pdf") -> ItemPendente:
    return ItemPendente(_arquivo(nome), status, "corpo parcial", 2)


def _contexto():
    handle = JobHandle(id=1, grupo="resumos", politica=Politica.LATEST_WINS)
    eventos: list = []
    return JobContext(handle, eventos.append), eventos


class _PainelFake:
    def __init__(self, falha=None):
        self._falha = falha
        self.textos: list[tuple] = []
        self.llm: list[str] = []
        self.resumos: list[tuple] = []
        self.guidances: list[tuple] = []

    def persistir_texto_definitivo(self, arquivo, status, texto, paginas=0):
        if self._falha == arquivo.nome:
            raise RuntimeError("boom")
        definitivo = f"{texto}|nota" if texto else "nota"
        self.textos.append((arquivo.nome, status, texto, paginas))
        return definitivo

    def gerar_e_persistir(self, arquivo, texto):
        self.llm.append(arquivo.nome)
        return ResumoDocumento("curto", "longo")

    def persistir_resumo_definitivo(self, arquivo, resumo):
        self.resumos.append((arquivo.nome, resumo))

    def avaliar_guidance(self, arquivo, texto, resumo=None):
        self.guidances.append((arquivo.nome, texto, resumo))
        return None


class TestExecutarFinalizacao:
    def test_parcial_persiste_texto_e_gera_resumo_via_llm(self):
        painel = _PainelFake()
        ctx, eventos = _contexto()

        executar_finalizacao(ctx, painel, [_item(StatusExtracao.PARCIAL)])

        assert painel.textos == [("10.pdf", StatusExtracao.PARCIAL, "corpo parcial", 2)]
        assert painel.llm == ["10.pdf"]
        assert painel.resumos == []
        assert painel.guidances[0][0] == "10.pdf"
        assert any(isinstance(e, Progresso) for e in eventos)

    def test_descreve_o_item_corrente_para_o_watchdog(self):
        painel = _PainelFake()
        ctx, _ = _contexto()

        executar_finalizacao(
            ctx,
            painel,
            [_item(StatusExtracao.PARCIAL, "10.pdf"), _item(
                StatusExtracao.FALHA, "20.pdf"
            )],
        )

        assert ctx.handle.descricao == "ALZR11/20.pdf"

    def test_falha_gera_resumo_deterministico_sem_llm(self):
        painel = _PainelFake()
        ctx, _ = _contexto()

        executar_finalizacao(ctx, painel, [_item(StatusExtracao.FALHA)])

        assert painel.llm == []
        assert [nome for nome, _ in painel.resumos] == ["10.pdf"]

    def test_protegido_gera_resumo_deterministico_sem_llm(self):
        painel = _PainelFake()
        ctx, _ = _contexto()

        executar_finalizacao(ctx, painel, [_item(StatusExtracao.PROTEGIDO)])

        assert painel.llm == []
        assert [nome for nome, _ in painel.resumos] == ["10.pdf"]

    def test_erro_por_item_nao_aborta_os_demais(self):
        painel = _PainelFake(falha="10.pdf")
        ctx, eventos = _contexto()

        executar_finalizacao(
            ctx,
            painel,
            [_item(StatusExtracao.PARCIAL, "10.pdf"), _item(
                StatusExtracao.FALHA, "20.pdf"
            )],
        )

        erros = [e for e in eventos if isinstance(e, Erro)]
        assert [e.dados.nome for e in erros] == ["10.pdf"]
        assert [nome for nome, _ in painel.resumos] == ["20.pdf"]
