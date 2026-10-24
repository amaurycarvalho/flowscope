"""Testes do read-model e da combinação de inferências de renda fixa."""

from datetime import date

from flowscope.domain.renda_fixa import (
    AusenciaFonte,
    CarteiraInferencias,
    CarteiraTitulos,
    InferenciaTitulo,
    PapelTitulo,
    TipoTitulo,
    TituloRendaFixa,
    cobertura_oficial_completa,
    montar_arvore,
)


def _inferencia(
    tipo: TipoTitulo = TipoTitulo.CRI,
    papel: PapelTitulo = PapelTitulo.DIREITO,
    descricao: str = "CRI da emissora Alfa",
) -> InferenciaTitulo:
    return InferenciaTitulo(
        tipo=tipo,
        papel=papel,
        descricao=descricao,
        documento="relatorio.pdf",
        chave_documento="documentos-relevantes/ALZR11/2026/02/10.pdf",
        hash_resumo="hash",
        trecho="O fundo mantém CRI da emissora Alfa.",
        confianca=0.82,
        data_referencia=date(2026, 2, 1),
    )


class TestInferenciaTitulo:
    def test_rotulos_e_proveniencia(self):
        item = _inferencia()
        assert item.inferido is True
        assert item.rotulo == "CRI da emissora Alfa"
        assert item.nome_exibicao == item.rotulo
        assert item.fonte == "LLM"
        assert item.id.startswith("i")
        assert len(item.id) == 11

    def test_id_estavel_e_distinto_por_conteudo(self):
        primeiro = _inferencia()
        assert primeiro.id == _inferencia().id
        assert primeiro.id != _inferencia(descricao="CRA da emissora Beta").id

    def test_carteira_vazia(self):
        assert CarteiraInferencias("ALZR11").vazio
        assert not CarteiraInferencias("ALZR11", itens=(_inferencia(),)).vazio


class TestCombinacao:
    def test_item_apenas_inferido_aparece(self):
        arvore = montar_arvore(None, [_inferencia()])
        tipos = {galho.tipo: galho for galho in arvore.direitos.tipos}
        assert isinstance(tipos[TipoTitulo.CRI].itens[0], InferenciaTitulo)

    def test_conflito_com_oficial_mantem_apenas_o_oficial(self):
        carteira = CarteiraTitulos(
            ticker="PETR4",
            tipo_ativo="acao",
            obrigacoes=(
                TituloRendaFixa(
                    tipo=TipoTitulo.DEBENTURE,
                    papel=PapelTitulo.OBRIGACAO,
                    id="d1",
                    identificacao="PETR27",
                ),
            ),
        )
        inferida = _inferencia(
            tipo=TipoTitulo.DEBENTURE,
            papel=PapelTitulo.OBRIGACAO,
            descricao="Debênture PETR27 emitida pela companhia",
        )

        arvore = montar_arvore(carteira, [inferida])

        tipos = {galho.tipo: galho for galho in arvore.obrigacoes.tipos}
        assert [item.id for item in tipos[TipoTitulo.DEBENTURE].itens] == ["d1"]

    def test_inferencia_remove_ausencia_explicita(self):
        carteira = CarteiraTitulos(
            ticker="PETR4",
            tipo_ativo="acao",
            ausencias=(
                AusenciaFonte(
                    TipoTitulo.CDB, PapelTitulo.OBRIGACAO, "sem fonte"
                ),
            ),
        )

        arvore = montar_arvore(
            carteira,
            [
                _inferencia(
                    tipo=TipoTitulo.CDB,
                    papel=PapelTitulo.OBRIGACAO,
                    descricao="CDB emitido pelo fundo",
                )
            ],
        )

        tipos = {galho.tipo: galho for galho in arvore.obrigacoes.tipos}
        assert all(
            not isinstance(item, AusenciaFonte)
            for item in tipos[TipoTitulo.CDB].itens
        )

    def test_ausencia_so_sem_oficial_e_sem_inferencia(self):
        carteira = CarteiraTitulos(ticker="PETR4", tipo_ativo="acao")
        arvore = montar_arvore(carteira)
        tipos = {galho.tipo: galho for galho in arvore.obrigacoes.tipos}
        assert isinstance(tipos[TipoTitulo.CDB].itens[0], AusenciaFonte)


class TestCoberturaOficial:
    def _carteira(self, obrigacoes=(), direitos=()) -> CarteiraTitulos:
        return CarteiraTitulos(
            ticker="ALZR11",
            tipo_ativo="fii",
            obrigacoes=obrigacoes,
            direitos=direitos,
        )

    def test_completa_com_os_dois_papeis(self):
        titulo = TituloRendaFixa(
            tipo=TipoTitulo.CRI, papel=PapelTitulo.DIREITO, id="c1"
        )
        obrigacao = TituloRendaFixa(
            tipo=TipoTitulo.DEBENTURE, papel=PapelTitulo.OBRIGACAO, id="d1"
        )
        assert cobertura_oficial_completa(
            self._carteira((obrigacao,), (titulo,))
        )

    def test_parcial_com_um_papel(self):
        titulo = TituloRendaFixa(
            tipo=TipoTitulo.CRI, papel=PapelTitulo.DIREITO, id="c1"
        )
        assert not cobertura_oficial_completa(self._carteira((), (titulo,)))

    def test_ausente_e_ausencia_explicita_sao_parciais(self):
        assert not cobertura_oficial_completa(None)
        carteira = CarteiraTitulos(
            ticker="PETR4",
            ausencias=(AusenciaFonte(TipoTitulo.CDB, PapelTitulo.OBRIGACAO),),
        )
        assert not cobertura_oficial_completa(carteira)
