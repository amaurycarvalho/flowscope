"""Testes do caso de uso de inferência de direitos e obrigações."""

import json
from datetime import date
from pathlib import Path

from flowscope.application.cancellation import OperacaoCancelada
from flowscope.application.renda_fixa import InferirDireitosObrigacoesUseCase
from flowscope.domain.documents import (
    AnoDocumentos,
    CatalogoTicker,
    CategoriaDocumentos,
    DocumentoArquivo,
    MesDocumentos,
)
from flowscope.domain.llm import LLMResposta
from flowscope.domain.renda_fixa import (
    CarteiraInferencias,
    CarteiraTitulos,
    InferenciaTitulo,
    PapelTitulo,
    TipoTitulo,
    TituloRendaFixa,
)


def _documento(
    nome: str,
    *,
    categoria: str = "Relatorio",
    resumo: str | None = "O fundo mantém CRI da emissora Alfa.",
    mes: int = 2,
) -> DocumentoArquivo:
    return DocumentoArquivo(
        ticker="ALZR11",
        ano=2026,
        mes=mes,
        categoria=categoria,
        nome=nome,
        tipo="pdf",
        caminho=Path("/cache") / categoria / nome,
        long_summary=resumo,
    )


class _CatalogoFake:
    def __init__(self, documentos):
        self._documentos = list(documentos)

    def catalogo(self, ticker):
        por_mes: dict[int, list[DocumentoArquivo]] = {}
        for documento in self._documentos:
            por_mes.setdefault(documento.mes, []).append(documento)
        meses = []
        for mes, itens in sorted(por_mes.items(), reverse=True):
            categorias: dict[str, list[DocumentoArquivo]] = {}
            for item in itens:
                categorias.setdefault(item.categoria, []).append(item)
            meses.append(
                MesDocumentos(
                    mes,
                    tuple(
                        CategoriaDocumentos(nome, tuple(arquivos))
                        for nome, arquivos in categorias.items()
                    ),
                )
            )
        return CatalogoTicker(ticker, (AnoDocumentos(2026, tuple(meses)),))


class _TitulosFake:
    def __init__(self, carteira=None):
        self._carteira = carteira

    def ler(self, ticker):
        return self._carteira

    def gravar(self, carteira):
        self._carteira = carteira


class _InferenciasFake:
    def __init__(self):
        self.carteiras: dict[str, CarteiraInferencias] = {}
        self.gravacoes = 0

    def ler(self, ticker):
        return self.carteiras.get(ticker)

    def gravar(self, carteira):
        self.carteiras[carteira.ticker] = carteira
        self.gravacoes += 1


class _LLMFake:
    def __init__(self, respostas=None, erro_na_chamada=None):
        self.respostas = list(respostas or [])
        self.erro_na_chamada = erro_na_chamada
        self.chamadas = 0

    def complete(self, messages, system_prompt=None):
        self.chamadas += 1
        if self.erro_na_chamada == self.chamadas:
            raise RuntimeError("llm falhou")
        texto = (
            self.respostas[min(self.chamadas - 1, len(self.respostas) - 1)]
            if self.respostas
            else _resposta_valida()
        )
        return LLMResposta(texto=texto)


def _resposta_valida(descricao: str = "CRI da emissora Alfa") -> str:
    return json.dumps(
        {
            "itens": [
                {
                    "tipo": "CRI",
                    "papel": "direito",
                    "descricao": descricao,
                    "documento": "relatorio.pdf",
                    "trecho": "O fundo mantém CRI da emissora Alfa.",
                    "confianca": 0.82,
                }
            ]
        }
    )


def _caso(
    documentos,
    *,
    carteira=None,
    llm=None,
    flag=True,
    inferencias=None,
) -> tuple[InferirDireitosObrigacoesUseCase, _LLMFake, _InferenciasFake]:
    llm = llm or _LLMFake()
    inferencias = inferencias or _InferenciasFake()
    caso = InferirDireitosObrigacoesUseCase(
        _CatalogoFake(documentos),
        _TitulosFake(carteira),
        inferencias,
        llm_factory=lambda: llm,
        llm_available=lambda: True,
        flag_habilitada=lambda: flag,
        base_dir=Path("/cache"),
    )
    return caso, llm, inferencias


class TestSelecao:
    def test_infere_apenas_rg_e_informe_com_resumo(self):
        documentos = [
            _documento("rg.pdf"),
            _documento("informe.html", categoria="Informe Mensal"),
            _documento("fato.pdf", categoria="Fato Relevante"),
            _documento("sem.pdf", resumo=None),
            _documento("truncado.pdf", resumo="resumo sem pontuacao"),
        ]
        caso, llm, inferencias = _caso(documentos)

        resultado = caso.executar("ALZR11")

        assert resultado.executada is True
        assert resultado.itens == 2
        assert llm.chamadas == 2
        assert len(inferencias.carteiras["ALZR11"].itens) == 2

    def test_reutiliza_cache_sem_nova_chamada(self):
        caso, llm, inferencias = _caso([_documento("rg.pdf")])

        primeiro = caso.executar("ALZR11")
        segundo = caso.executar("ALZR11")

        assert primeiro.itens == 1
        assert segundo.executada is False
        assert llm.chamadas == 1
        assert len(inferencias.carteiras["ALZR11"].itens) == 1

    def test_resumo_alterado_substitui_a_inferencia(self):
        documento = _documento("rg.pdf")
        caso, llm, inferencias = _caso([documento])
        caso.executar("ALZR11")

        documento_modificado = _documento(
            "rg.pdf", resumo="O fundo passou a manter CRA da emissora Beta."
        )
        caso._catalogo = _CatalogoFake([documento_modificado])
        resultado = caso.executar("ALZR11")

        assert resultado.itens == 1
        assert llm.chamadas == 2
        itens = inferencias.carteiras["ALZR11"].itens
        assert len(itens) == 1
        assert itens[0].hash_resumo != ""


class TestValidacao:
    def test_descarta_tipo_desconhecido_e_item_sem_evidencia(self):
        resposta = json.dumps(
            {
                "itens": [
                    {
                        "tipo": "desconhecido",
                        "papel": "direito",
                        "descricao": "x",
                        "documento": "relatorio.pdf",
                        "trecho": "x",
                    },
                    {
                        "tipo": "CRI",
                        "papel": "direito",
                        "descricao": "sem evidência",
                        "documento": "relatorio.pdf",
                    },
                    {
                        "tipo": "CRI",
                        "papel": "direito",
                        "descricao": "válido",
                        "documento": "relatorio.pdf",
                        "trecho": "evidência",
                        "confianca": 0.9,
                    },
                ]
            }
        )
        caso, _, inferencias = _caso(
            [_documento("rg.pdf")], llm=_LLMFake([resposta])
        )

        resultado = caso.executar("ALZR11")

        assert resultado.itens == 1
        itens = inferencias.carteiras["ALZR11"].itens
        assert [item.descricao for item in itens] == ["válido"]


class TestElegibilidade:
    def test_flag_desligada_nao_chama_llm(self):
        caso, llm, _ = _caso([_documento("rg.pdf")], flag=False)

        assert caso.precisa_inferencia("ALZR11") is False
        assert caso.executar("ALZR11").executada is False
        assert llm.chamadas == 0

    def test_cobertura_completa_nao_infere(self):
        carteira = CarteiraTitulos(
            ticker="ALZR11",
            tipo_ativo="fii",
            obrigacoes=(
                TituloRendaFixa(
                    TipoTitulo.DEBENTURE, PapelTitulo.OBRIGACAO, id="d1"
                ),
            ),
            direitos=(
                TituloRendaFixa(TipoTitulo.CRI, PapelTitulo.DIREITO, id="c1"),
            ),
        )
        caso, llm, _ = _caso([_documento("rg.pdf")], carteira=carteira)

        assert caso.precisa_inferencia("ALZR11") is False
        assert caso.executar("ALZR11").executada is False
        assert llm.chamadas == 0

    def test_cobertura_parcial_infere(self):
        carteira = CarteiraTitulos(
            ticker="ALZR11",
            tipo_ativo="fii",
            direitos=(
                TituloRendaFixa(TipoTitulo.CRI, PapelTitulo.DIREITO, id="c1"),
            ),
        )
        caso, llm, _ = _caso([_documento("rg.pdf")], carteira=carteira)

        assert caso.precisa_inferencia("ALZR11") is True
        assert caso.executar("ALZR11").executada is True
        assert llm.chamadas == 1


class TestFalhaECancelamento:
    def test_falha_em_um_documento_nao_impede_os_demais(self):
        caso, _, inferencias = _caso(
            [_documento("rg1.pdf"), _documento("rg2.pdf")],
            llm=_LLMFake([_resposta_valida()], erro_na_chamada=1),
        )

        resultado = caso.executar("ALZR11")

        assert resultado.falhas == 1
        assert resultado.itens == 1
        assert len(inferencias.carteiras["ALZR11"].itens) == 1

    def test_cancelamento_preserva_itens_ja_gravados(self):
        chamadas = {"total": 0}

        def cancelar():
            chamadas["total"] += 1
            if chamadas["total"] >= 3:
                raise OperacaoCancelada()

        caso, _, inferencias = _caso(
            [_documento("rg1.pdf"), _documento("rg2.pdf")]
        )

        resultado = caso.executar("ALZR11", cancelar=cancelar)

        assert resultado.cancelada is True
        assert resultado.itens == 1
        assert len(inferencias.carteiras["ALZR11"].itens) == 1


def _item_inferido() -> InferenciaTitulo:
    return InferenciaTitulo(
        tipo=TipoTitulo.CRI,
        papel=PapelTitulo.DIREITO,
        descricao="CRI",
        documento="rg.pdf",
        chave_documento="rg.pdf",
        hash_resumo="hash",
        trecho="evidência",
        data_referencia=date(2026, 2, 1),
    )
