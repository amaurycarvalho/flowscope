"""Testes do extrator de arquivo com orçamento de tempo.

Rodam em qualquer máquina: usam o PDF pequeno de fixture do repositório e o
auxiliar puro de acumulação (independente de PDF real). Não dependem do PDF
patológico que motivou a change.
"""

import base64
import logging
import multiprocessing
from io import BytesIO
from pathlib import Path

import pypdf

from flowscope.application import extracao_orcada
from flowscope.application.document_preview import (
    SELETOR_CONTEUDO_DETALHE,
    ExtracaoTexto,
    StatusExtracao,
)
from flowscope.application.extracao_orcada import (
    EXTRACAO_TIMEOUT_S,
    extrair_arquivo_com_orcamento,
)
from flowscope.presentation.gui.background.manager import LIMITE_INATIVIDADE_S

_FIXTURE_PDF = (
    Path(__file__).resolve().parent.parent
    / "fixtures"
    / "b3"
    / "bdr_aviso_exxo.pdf.b64"
)


def _pdf_com_texto() -> bytes:
    return base64.b64decode(_FIXTURE_PDF.read_text(encoding="ascii"))


def _pdf_cifrado(senha: str) -> bytes:
    leitor = pypdf.PdfReader(BytesIO(_pdf_com_texto()))
    escritor = pypdf.PdfWriter()
    for pagina in leitor.pages:
        escritor.add_page(pagina)
    escritor.encrypt(senha)
    buffer = BytesIO()
    escritor.write(buffer)
    return buffer.getvalue()


def _pdf_vazio() -> bytes:
    escritor = pypdf.PdfWriter()
    escritor.add_blank_page(width=200, height=200)
    buffer = BytesIO()
    escritor.write(buffer)
    return buffer.getvalue()


class _RelogioFake:
    def __init__(self) -> None:
        self.t = 0.0

    def agora(self) -> float:
        return self.t


class _FonteRoteirizada:
    """Fonte de mensagens que devolve um roteiro e depois ``None`` (timeout)."""

    def __init__(self, mensagens: list[tuple]) -> None:
        self._mensagens = list(mensagens)

    def ler(self, _timeout: float) -> tuple | None:
        if not self._mensagens:
            return None
        return self._mensagens.pop(0)


class TestAuxiliarPuro:
    def test_consumir_acumula_ate_o_fim(self):
        fonte = _FonteRoteirizada(
            [
                (extracao_orcada._PAGINA, "boa", False),
                (extracao_orcada._PAGINA, "", True),
                (extracao_orcada._FIM,),
            ]
        )
        acumulado = extracao_orcada._consumir(
            fonte, 10.0, _RelogioFake().agora
        )
        assert acumulado.concluiu is True
        assert acumulado.textos == ("boa",)
        assert acumulado.falhas == 1

    def test_consumir_estouro_preserva_textos(self):
        fonte = _FonteRoteirizada(
            [(extracao_orcada._PAGINA, "primeira", False)]
        )
        acumulado = extracao_orcada._consumir(
            fonte, 10.0, _RelogioFake().agora
        )
        assert acumulado.concluiu is False
        assert acumulado.textos == ("primeira",)

    def test_consumir_resultado_prevalece(self):
        fonte = _FonteRoteirizada(
            [(extracao_orcada._RESULTADO, "", StatusExtracao.FALHA.value, 0)]
        )
        acumulado = extracao_orcada._consumir(
            fonte, 10.0, _RelogioFake().agora
        )
        assert acumulado.concluiu is True
        assert acumulado.resultado is not None
        assert acumulado.resultado.status is StatusExtracao.FALHA

    def test_estouro_com_texto_resulta_parcial(self):
        acumulado = extracao_orcada._Acumulado(("texto parcial",), 0, False)
        resultado = extracao_orcada._resultado_de(acumulado)
        assert resultado.status is StatusExtracao.PARCIAL
        assert resultado.texto == "texto parcial"

    def test_estouro_sem_texto_resulta_falha(self):
        acumulado = extracao_orcada._Acumulado((), 0, False)
        resultado = extracao_orcada._resultado_de(acumulado)
        assert resultado.status is StatusExtracao.FALHA
        assert resultado.texto == ""


class TestIntegracao:
    def test_pdf_pequeno_dentro_do_orcamento(self, tmp_path):
        caminho = tmp_path / "doc.pdf"
        caminho.write_bytes(_pdf_com_texto())
        resultado = extrair_arquivo_com_orcamento(caminho)
        assert resultado.status is StatusExtracao.OK
        assert resultado.texto.strip()

    def test_orcamento_nulo_encerra_o_filho(self, tmp_path):
        caminho = tmp_path / "doc.pdf"
        caminho.write_bytes(_pdf_com_texto())
        antes = set(multiprocessing.active_children())
        resultado = extrair_arquivo_com_orcamento(caminho, timeout=0.0)
        assert resultado.status is StatusExtracao.FALHA
        assert resultado.texto == ""
        novos = set(multiprocessing.active_children()) - antes
        assert novos == set()

    def test_html_eh_imediato(self, tmp_path):
        caminho = tmp_path / "noticia.html"
        caminho.write_text(
            "<html><body><div>Moldura</div>"
            "<pre id='conteudoDetalhe'>Corpo do artigo</pre></body></html>",
            encoding="utf-8",
        )
        resultado = extrair_arquivo_com_orcamento(caminho, SELETOR_CONTEUDO_DETALHE)
        assert resultado.status is StatusExtracao.OK
        assert resultado.texto == "Corpo do artigo"

    def test_senha_repassada_ao_pdf(self, tmp_path):
        caminho = tmp_path / "cifrado.pdf"
        caminho.write_bytes(_pdf_cifrado("segredo"))
        assert (
            extrair_arquivo_com_orcamento(caminho, senha="segredo").status
            is StatusExtracao.OK
        )
        assert (
            extrair_arquivo_com_orcamento(caminho, senha="errada").status
            is StatusExtracao.PROTEGIDO
        )


class TestPreservacaoSemTexto:
    def test_pdf_sem_texto_permanece_sem_texto(self, tmp_path):
        caminho = tmp_path / "vazio.pdf"
        caminho.write_bytes(_pdf_vazio())
        assert (
            extrair_arquivo_com_orcamento(caminho).status
            is StatusExtracao.SEM_TEXTO
        )

    def test_estouro_nao_e_sem_texto(self, tmp_path):
        caminho = tmp_path / "doc.pdf"
        caminho.write_bytes(_pdf_com_texto())
        resultado = extrair_arquivo_com_orcamento(caminho, timeout=0.0)
        assert resultado.status is not StatusExtracao.SEM_TEXTO
        assert resultado.status is StatusExtracao.FALHA


class TestResultadoDe:
    def test_resultado_explicito_prevalece(self):
        esperado = ExtracaoTexto("", StatusExtracao.PROTEGIDO)
        acumulado = extracao_orcada._Acumulado((), 0, True, esperado)
        assert extracao_orcada._resultado_de(acumulado) is esperado


class TestOrcamentoVsWatchdog:
    def test_orcamento_abaixo_do_limite_de_inatividade(self):
        # A extração bloqueia o worker sem progresso; um orçamento >= ao limite
        # de inatividade faria o watchdog encerrar o lote por inatividade.
        assert EXTRACAO_TIMEOUT_S < LIMITE_INATIVIDADE_S


class TestLogPypdf:
    @staticmethod
    def _isolar(monkeypatch):
        logger = logging.getLogger("pypdf")
        monkeypatch.setattr(logger, "handlers", [])
        monkeypatch.setattr(logger, "level", logging.NOTSET)
        monkeypatch.setattr(logger, "propagate", True)
        return logger

    def test_disca_warning_e_grava_error(self, tmp_path, monkeypatch):
        logger = self._isolar(monkeypatch)
        destino = tmp_path / "flowscope.log"

        extracao_orcada._configurar_log_pypdf(destino)
        logger.warning("Ignoring wrong pointing object 1 0 (offset 0)")
        logger.error("falha real do pypdf")
        for handler in list(logger.handlers):
            handler.flush()

        conteudo = destino.read_text(encoding="utf-8")
        assert "Ignoring wrong pointing" not in conteudo
        assert "falha real do pypdf" in conteudo
        assert "ERROR" in conteudo
        for handler in list(logger.handlers):
            handler.close()

    def test_idempotente(self, tmp_path, monkeypatch):
        logger = self._isolar(monkeypatch)
        destino = tmp_path / "flowscope.log"

        extracao_orcada._configurar_log_pypdf(destino)
        extracao_orcada._configurar_log_pypdf(destino)

        arquivos = [
            h for h in logger.handlers if isinstance(h, logging.FileHandler)
        ]
        assert len(arquivos) == 1
        for handler in arquivos:
            handler.close()
