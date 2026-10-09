"""Testes do manifesto estável da árvore de conhecimento."""

from pathlib import Path

from flowscope.application.chat.arvore import (
    ArvoreConhecimento,
    no_folha,
    no_interno,
    ramo_flowscope,
    ramo_fundamentos,
)
from flowscope.application.chat.manifesto import (
    TETO_TOKENS,
    assinatura_estado,
    estimar_tokens,
    montar_manifesto,
)


def _arvore() -> ArvoreConhecimento:
    raiz = no_interno("/", "raiz")
    raiz.filho(
        ramo_fundamentos(
            tickers=["PETR4", "VALE3"],
            campos={"PL": "preço/lucro"},
            valores={"PETR4": "[PETR4] PL=3.2"},
        )
    )
    return ArvoreConhecimento(raiz, assinatura="sig")


def _arvore_completa() -> ArvoreConhecimento:
    """Árvore com todos os ramos de topo, para o mapa canônico completo."""
    raiz = no_interno("/", "raiz")
    raiz.filho(
        ramo_flowscope(
            {"versao": "1.0"},
            abas={"Chat AI": "chat"},
            indicadores={"RSI": "índice de força"},
        )
    )
    raiz.filho(
        ramo_fundamentos(
            tickers=["PETR4"],
            campos={"PL": "preço/lucro"},
            valores={"PETR4": "[PETR4] PL=3.2"},
        )
    )
    for caminho, nome in (
        ("/documentos", "documentos"),
        ("/guidance", "guidance"),
        ("/direitos-obrigacoes", "direitos e obrigacoes"),
        ("/noticias", "noticias"),
    ):
        raiz.filho(no_interno(caminho, nome))
    return ArvoreConhecimento(raiz, assinatura="sig")


def _ramo_guidance() -> object:
    raiz = no_interno("/guidance", "guidance")
    ticker = no_interno("/guidance/HGBS11", "HGBS11")
    ano = no_interno("/guidance/HGBS11/2026", "2026")
    mes = no_interno("/guidance/HGBS11/2026/08", "08")
    mes.filho(
        no_folha(
            "/guidance/HGBS11/2026/08/g1",
            "Guidance R$ 0,85/cota",
            metadado="Relatório Gerencial — ago/26 (1323324.pdf)",
            conteudo="Guidance R$ 0,85/cota (2026, ago/26)",
        )
    )
    ano.filho(mes)
    ticker.filho(ano)
    raiz.filho(ticker)
    return raiz


def _ramo_direitos() -> object:
    raiz = no_interno("/direitos-obrigacoes", "direitos e obrigacoes")
    raiz.filho(
        no_folha(
            "/direitos-obrigacoes/direitos",
            "direitos",
            conteudo="Sem dados de Direitos.",
        )
    )
    raiz.filho(
        no_folha(
            "/direitos-obrigacoes/obrigacoes",
            "obrigacoes",
            conteudo="Sem dados de Obrigações.",
        )
    )
    return raiz


class TestManifesto:
    def test_determinismo(self) -> None:
        arvore = _arvore()
        assert montar_manifesto(arvore) == montar_manifesto(arvore)

    def test_inclui_chaves(self) -> None:
        texto = montar_manifesto(_arvore())
        assert "PETR4" in texto and "VALE3" in texto
        assert "listar" in texto and "buscar_semantico" in texto

    def test_protocolo_orienta_busca_deterministica(self) -> None:
        texto = montar_manifesto(_arvore())
        assert "indice_indisponivel" in texto
        assert "buscar(caminho, regex" in texto
        assert "busca determinística" in texto

    def test_inclui_mapa_da_arvore(self) -> None:
        texto = montar_manifesto(_arvore_completa())
        assert "/documentos/<ticker>/indice" in texto
        assert "/documentos/<ticker>/<chave>/curto" in texto
        assert "/noticias/<grupo>/indice" in texto
        assert "/fundamentos/valores/<ticker>" in texto
        assert "/guidance/<ticker>/indice" in texto
        assert "/flowscope/abas/<aba>" in texto
        assert "/direitos-obrigacoes/direitos" in texto

    def test_mapa_omite_ramos_inexistentes(self) -> None:
        texto = montar_manifesto(_arvore())
        assert "/documentos/<ticker>/indice" not in texto
        assert "/guidance/<ticker>" not in texto
        assert "/direitos-obrigacoes/direitos" not in texto

    def test_playbook_por_intencao(self) -> None:
        texto = montar_manifesto(_arvore_completa())
        assert "Playbook por intenção" in texto
        assert "Resumo curto" in texto
        assert "Resumo longo" in texto
        assert "/curto" in texto and "/longo" in texto
        assert "prévia" in texto
        assert "texto integral" in texto
        assert "Relatório Gerencial mensal" in texto
        assert "/documentos/<ticker>/indice" in texto
        assert "/flowscope/abas/<aba>/subabas/<sub>" in texto

    def test_protocolo_orienta_nao_procrastinar_e_foco(self) -> None:
        texto = montar_manifesto(_arvore_completa())
        assert "### Como responder" in texto
        assert "prometendo navegar" in texto
        assert "foco" in texto

    def test_orienta_paginacao_de_textos_longos(self) -> None:
        texto = montar_manifesto(_arvore_completa())
        assert "offset" in texto
        assert "limite" in texto
        assert "continua" in texto

    def test_metadado_de_documento_nao_integra_manifesto(self) -> None:
        raiz = no_interno("/", "raiz")
        doc = no_interno("/documentos/PETR4", "PETR4")
        doc.filho(
            no_folha("/documentos/PETR4/d1/longo", "longo", metadado="resumo longo")
        )
        raiz.filho(doc)
        texto = montar_manifesto(ArvoreConhecimento(raiz, assinatura="s"))
        assert "/documentos/PETR4/d1/longo:" not in texto

    def test_subabas_listadas(self) -> None:
        raiz = no_interno("/", "raiz")
        raiz.filho(
            ramo_flowscope(
                {"versao": "1.0"},
                abas={"Análise Geral": "x"},
                subabas={"Análise Geral": {"Fundamentos": "texto"}},
            )
        )
        texto = montar_manifesto(ArvoreConhecimento(raiz, assinatura="s"))
        assert "- subabas Análise Geral: Fundamentos" in texto

    def test_metadado_longo_omitido(self) -> None:
        raiz = no_interno("/", "raiz")
        raiz.filho(no_folha("/x", "x", metadado="y" * 200))
        raiz.filho(no_folha("/y", "nome", metadado="curto"))
        texto = montar_manifesto(ArvoreConhecimento(raiz))
        assert "## Metadados" in texto
        assert "y" * 200 not in texto
        assert "curto" in texto

    def test_metadado_redundante_omitido(self) -> None:
        raiz = no_interno("/", "raiz")
        raiz.filho(no_folha("/x", "x", metadado="x"))
        texto = montar_manifesto(ArvoreConhecimento(raiz))
        assert "## Metadados" not in texto

    def test_estima_tokens(self) -> None:
        assert estimar_tokens("x" * 400) == 100

    def test_teto_respeitado(self) -> None:
        assert estimar_tokens(montar_manifesto(_arvore())) < TETO_TOKENS

    def test_teto_com_ramos_novos(self) -> None:
        raiz = no_interno("/", "raiz")
        raiz.filho(
            ramo_flowscope(
                {"versao": "1.0"},
                abas={"Análise Geral": "painéis gerais"},
                subabas={"Análise Geral": {"Fundamentos": "métricas"}},
            )
        )
        raiz.filho(_ramo_guidance())
        raiz.filho(_ramo_direitos())
        raiz.filho(
            ramo_fundamentos(
                tickers=["PETR4", "VALE3"],
                valores={"PETR4": "[PETR4] PL=3.2"},
            )
        )
        arvore = ArvoreConhecimento(raiz, assinatura="sig")
        texto = montar_manifesto(arvore)
        assert estimar_tokens(texto) < TETO_TOKENS
        assert texto == montar_manifesto(arvore)

    def test_degrada_para_so_chaves(self) -> None:
        raiz = no_interno("/", "raiz")
        raiz.filho(no_folha("/x", "x", metadado="propósito descritivo"))
        arvore = ArvoreConhecimento(raiz)
        sem_degradar = montar_manifesto(arvore)
        assert "## Metadados" in sem_degradar
        degradado = montar_manifesto(arvore, contar_tokens=lambda _t: TETO_TOKENS + 1)
        assert "## Metadados" not in degradado


class TestAssinatura:
    def test_estavel_para_mesma_entrada(self, tmp_path: Path) -> None:
        arquivo = tmp_path / "a.txt"
        arquivo.write_text("x")
        a = assinatura_estado([arquivo], ["PETR4"])
        b = assinatura_estado([arquivo], ["PETR4"])
        assert a == b

    def test_muda_com_watchlist(self, tmp_path: Path) -> None:
        arquivo = tmp_path / "a.txt"
        arquivo.write_text("x")
        assert assinatura_estado([arquivo], ["PETR4"]) != assinatura_estado(
            [arquivo], ["VALE3"]
        )

    def test_muda_com_mtime(self, tmp_path: Path) -> None:
        arquivo = tmp_path / "a.txt"
        arquivo.write_text("x")
        antes = assinatura_estado([arquivo], [])
        import os

        os.utime(arquivo, ns=(1, 2_000_000_000))
        assert assinatura_estado([arquivo], []) != antes

    def test_tolera_arquivo_ausente(self, tmp_path: Path) -> None:
        assert assinatura_estado([tmp_path / "some.txt"], []) == assinatura_estado(
            [tmp_path / "some.txt"], []
        )
