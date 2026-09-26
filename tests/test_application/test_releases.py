"""Testes puros da verificação de nova versão publicada."""

from flowscope.application.releases import verificar_nova_versao


class TestVerificarNovaVersao:
    def test_versao_mais_nova_retorna_info(self):
        resultado = verificar_nova_versao("1.0.0", lambda: ("1.1.0", "url"))
        assert resultado == ("1.1.0", "url")

    def test_versao_igual_nao_retorna(self):
        assert verificar_nova_versao("1.1.0", lambda: ("1.1.0", "url")) is None

    def test_versao_anterior_nao_retorna(self):
        assert verificar_nova_versao("1.1.0", lambda: ("1.0.0", "url")) is None

    def test_sem_resultado_retorna_none(self):
        assert verificar_nova_versao("1.0.0", lambda: None) is None

    def test_checker_e_consultado(self):
        chamadas: list[int] = []

        def checker():
            chamadas.append(1)
            return None

        verificar_nova_versao("1.0.0", checker)
        assert chamadas == [1]
