"""Testes da política central de erros HTTP e do motor de retry."""

from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

import pytest
import requests

from flowscope.application.cancellation import OperacaoCancelada
from flowscope.infrastructure.http_retry import (
    Categoria,
    classificar,
    executar_com_retry,
)


class _Resposta:
    def __init__(self, status: int, headers: dict[str, str] | None = None) -> None:
        self.status_code = status
        self.headers = headers or {}


def _erro(status: int, headers: dict[str, str] | None = None) -> requests.HTTPError:
    erro = requests.HTTPError(f"HTTP {status}")
    erro.response = _Resposta(status, headers)
    return erro


class TestClassificar:
    @pytest.mark.parametrize(
        ("status", "esperada"),
        [
            (403, Categoria.PERMANENTE),
            (404, Categoria.PERMANENTE),
            (400, Categoria.PERMANENTE),
            (408, Categoria.TRANSITORIO),
            (425, Categoria.TRANSITORIO),
            (429, Categoria.THROTTLE),
            (500, Categoria.TRANSITORIO),
            (501, Categoria.PERMANENTE),
            (502, Categoria.TRANSITORIO),
            (504, Categoria.TRANSITORIO),
            (505, Categoria.PERMANENTE),
            (506, Categoria.PERMANENTE),
            (511, Categoria.PERMANENTE),
            (520, Categoria.GATEWAY),
            (521, Categoria.GATEWAY),
            (522, Categoria.GATEWAY),
            (523, Categoria.GATEWAY),
            (524, Categoria.GATEWAY),
        ],
    )
    def test_classifica_codigos(self, status, esperada):
        assert classificar(status) is esperada

    def test_503_sem_retry_after_e_transitorio(self):
        assert classificar(503) is Categoria.TRANSITORIO

    def test_503_com_retry_after_e_throttle(self):
        assert classificar(503, {"Retry-After": "5"}) is Categoria.THROTTLE

    def test_retry_after_case_insensitive(self):
        assert classificar(503, {"retry-after": "5"}) is Categoria.THROTTLE


class TestMetodosRepetiveis:
    def _fn_que_falha(self, erro, tentativas):
        def fn():
            tentativas["n"] += 1
            if tentativas["n"] < 2:
                raise erro
            return "ok"

        return fn

    def test_get_repete_em_transitorio(self):
        tentativas = {"n": 0}
        fn = self._fn_que_falha(_erro(502), tentativas)
        resultado = executar_com_retry(
            fn, metodo="GET", delays=(0, 0), sleep=lambda _: None
        )
        assert resultado == "ok"
        assert tentativas["n"] == 2

    def test_post_marcado_repete(self):
        tentativas = {"n": 0}
        fn = self._fn_que_falha(_erro(504), tentativas)
        resultado = executar_com_retry(
            fn,
            metodo="POST",
            repetivel=True,
            delays=(0, 0),
            sleep=lambda _: None,
        )
        assert resultado == "ok"
        assert tentativas["n"] == 2

    def test_post_nao_marcado_nao_repete(self):
        tentativas = {"n": 0}
        fn = self._fn_que_falha(_erro(500), tentativas)
        with pytest.raises(requests.HTTPError):
            executar_com_retry(
                fn, metodo="POST", delays=(0, 0), sleep=lambda _: None
            )
        assert tentativas["n"] == 1


class TestEspera:
    def test_retry_after_em_segundos(self):
        esperas: list[float] = []
        tentativas = {"n": 0}

        def fn():
            tentativas["n"] += 1
            if tentativas["n"] < 2:
                raise _erro(429, {"Retry-After": "5"})
            return "ok"

        executar_com_retry(
            fn,
            metodo="GET",
            delays=(0, 1),
            sleep=esperas.append,
            jitter=lambda: 0.0,
        )
        assert esperas == [5.0]

    def test_retry_after_em_data_http(self):
        esperas: list[float] = []
        tentativas = {"n": 0}
        futuro = datetime.now(timezone.utc) + timedelta(seconds=10)
        cabecalho = format_datetime(futuro, usegmt=True)

        def fn():
            tentativas["n"] += 1
            if tentativas["n"] < 2:
                raise _erro(429, {"Retry-After": cabecalho})
            return "ok"

        executar_com_retry(
            fn,
            metodo="GET",
            delays=(0, 1),
            sleep=esperas.append,
            jitter=lambda: 0.0,
        )
        assert len(esperas) == 1
        assert 8.0 <= esperas[0] <= 10.0

    def test_retry_after_acima_do_teto(self):
        esperas: list[float] = []
        tentativas = {"n": 0}

        def fn():
            tentativas["n"] += 1
            if tentativas["n"] < 2:
                raise _erro(429, {"Retry-After": "1000"})
            return "ok"

        executar_com_retry(
            fn,
            metodo="GET",
            delays=(0, 1),
            sleep=esperas.append,
            jitter=lambda: 0.0,
        )
        assert esperas == [60.0]

    def test_gateway_espera_mais_que_transitorio(self):
        def espera_para(status: int) -> float:
            esperas: list[float] = []
            tentativas = {"n": 0}

            def fn():
                tentativas["n"] += 1
                if tentativas["n"] < 2:
                    raise _erro(status)
                return "ok"

            executar_com_retry(
                fn,
                metodo="GET",
                delays=(0, 1, 3, 10),
                sleep=esperas.append,
                jitter=lambda: 0.0,
            )
            return esperas[0]

        assert espera_para(522) > espera_para(502)

    def test_jitter_multiplica_o_backoff(self):
        esperas: list[float] = []
        tentativas = {"n": 0}

        def fn():
            tentativas["n"] += 1
            if tentativas["n"] < 2:
                raise _erro(502)
            return "ok"

        executar_com_retry(
            fn,
            metodo="GET",
            delays=(0, 4),
            sleep=esperas.append,
            jitter=lambda: 0.5,
        )
        assert esperas == [6.0]


class TestOverride:
    def test_404_repetido_por_override(self):
        tentativas = {"n": 0}

        def fn():
            tentativas["n"] += 1
            if tentativas["n"] < 2:
                raise _erro(404)
            return "ok"

        resultado = executar_com_retry(
            fn,
            metodo="GET",
            transitorios_extra=frozenset({404}),
            delays=(0, 0),
            sleep=lambda _: None,
        )
        assert resultado == "ok"
        assert tentativas["n"] == 2

    def test_sem_override_404_nao_repete(self):
        tentativas = {"n": 0}

        def fn():
            tentativas["n"] += 1
            raise _erro(404)

        with pytest.raises(requests.HTTPError):
            executar_com_retry(fn, metodo="GET", delays=(0, 0), sleep=lambda _: None)
        assert tentativas["n"] == 1


class TestCancelamento:
    def test_cancelamento_interrompe_a_espera(self):
        chamadas = {"n": 0}
        pedido = {"cancelar": False}

        def fn():
            chamadas["n"] += 1
            raise requests.ConnectionError("rede fora")

        def cancelar():
            if pedido["cancelar"]:
                raise OperacaoCancelada()

        def dormir(_segundos):
            pedido["cancelar"] = True

        with pytest.raises(OperacaoCancelada):
            executar_com_retry(
                fn,
                metodo="GET",
                delays=(0, 1, 3),
                sleep=dormir,
                cancelar=cancelar,
            )
        assert chamadas["n"] == 1


class TestRegistro:
    def test_permanente_registra_status_e_categoria(self, caplog):
        def fn():
            raise _erro(403)

        with caplog.at_level("WARNING", logger="flowscope.infrastructure.http_retry"):
            with pytest.raises(requests.HTTPError):
                executar_com_retry(
                    fn, metodo="GET", delays=(0, 1), sleep=lambda _: None
                )
        assert "403" in caplog.text
        assert "permanente" in caplog.text

    def test_esgotamento_registra_categoria(self, caplog):
        def fn():
            raise requests.ConnectionError("rede fora")

        with caplog.at_level("WARNING", logger="flowscope.infrastructure.http_retry"):
            with pytest.raises(requests.ConnectionError):
                executar_com_retry(
                    fn, metodo="GET", delays=(0, 0), sleep=lambda _: None
                )
        assert "transitorio" in caplog.text
        assert "esgotadas" in caplog.text
