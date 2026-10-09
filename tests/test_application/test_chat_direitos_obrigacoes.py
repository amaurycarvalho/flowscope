"""Testes da fonte do ramo ``/direitos-obrigacoes`` da árvore de conhecimento."""

from flowscope.application.chat.arvore import ArvoreConhecimento, no_interno
from flowscope.application.chat.direitos_obrigacoes import (
    FonteDireitosObrigacoes,
)


def _arvore() -> ArvoreConhecimento:
    raiz = no_interno("/", "/")
    raiz.filho(FonteDireitosObrigacoes().construir())
    return ArvoreConhecimento(raiz)


class TestFonteDireitosObrigacoes:
    def test_lista_sub_ramos(self):
        nomes = [no.nome for no in _arvore().listar("/direitos-obrigacoes")]
        assert nomes == ["direitos", "obrigacoes"]

    def test_nos_vazios_sao_navegaveis(self):
        arvore = _arvore()
        assert "Sem dados de Direitos." in arvore.obter(
            "/direitos-obrigacoes/direitos"
        )
        assert "Sem dados de Obrigações." in arvore.obter(
            "/direitos-obrigacoes/obrigacoes"
        )
