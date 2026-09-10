import json
from datetime import date, datetime, timedelta, timezone

from flowscope.infrastructure.cache import CacheManager
from flowscope.infrastructure.conditional_cache import (
    DATA_ULTIMA_COTACAO,
    ETAG,
    REVALIDATED_AT,
    CacheOutcome,
    CacheRecord,
    ConditionalCache,
    DateValidator,
    Fetched,
    HttpValidator,
    RevalidationResult,
    RevalidationStatus,
)


class _Clock:
    def __init__(self, inicio: datetime | None = None) -> None:
        self.agora = inicio or datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self.agora

    def avancar(self, delta: timedelta) -> None:
        self.agora += delta


class _Response:
    def __init__(self, text: str = "", status: int = 200, headers: dict | None = None) -> None:
        self.text = text
        self.status_code = status
        self.headers = headers or {}


class _Fetcher:
    def __init__(self, respostas) -> None:
        self._respostas = respostas if isinstance(respostas, Exception) else list(respostas)
        self.chamadas = 0

    def __call__(self, validators):
        self.chamadas += 1
        if isinstance(self._respostas, Exception):
            raise self._respostas
        return self._respostas.pop(0)


class _FixedValidator:
    def __init__(self, resultado: RevalidationResult) -> None:
        self._resultado = resultado
        self.chamadas = 0

    def revalidate(self, record: CacheRecord) -> RevalidationResult:
        self.chamadas += 1
        return self._resultado


def _cache(tmp_path, clock) -> ConditionalCache:
    return ConditionalCache(cache=CacheManager(cache_dir=tmp_path), now=clock)


class TestGetOrRevalidate:
    def test_miss_armazena_e_depois_hit_sem_rede(self, tmp_path):
        clock = _Clock()
        cache = _cache(tmp_path, clock)
        chamadas = []

        def fetch() -> Fetched:
            chamadas.append(1)
            return Fetched("conteudo", {ETAG: "v1"})

        resultado = cache.get_or_revalidate("k", fetch=fetch, freshness=timedelta(hours=1))
        assert resultado.outcome is CacheOutcome.MISS
        assert resultado.value == "conteudo"

        resultado2 = cache.get_or_revalidate("k", fetch=fetch, freshness=timedelta(hours=1))
        assert resultado2.outcome is CacheOutcome.HIT
        assert len(chamadas) == 1

    def test_revalidado_quando_validador_inalterado(self, tmp_path):
        clock = _Clock()
        cache = _cache(tmp_path, clock)
        cache.get_or_revalidate(
            "k", fetch=lambda: Fetched("antigo", {}), freshness=timedelta(0)
        )
        clock.avancar(timedelta(hours=2))
        validador = _FixedValidator(
            RevalidationResult(RevalidationStatus.UNCHANGED, validators={ETAG: "v2"})
        )
        resultado = cache.get_or_revalidate(
            "k", fetch=lambda: Fetched("novo", {}), validators=[validador]
        )
        assert resultado.outcome is CacheOutcome.REVALIDATED
        assert resultado.value == "antigo"
        assert validador.chamadas == 1

    def test_atualizado_quando_validador_detecta_mudanca(self, tmp_path):
        clock = _Clock()
        cache = _cache(tmp_path, clock)
        cache.get_or_revalidate("k", fetch=lambda: Fetched("antigo", {}))
        clock.avancar(timedelta(hours=2))
        validador = _FixedValidator(
            RevalidationResult(RevalidationStatus.CHANGED, payload="novo")
        )
        resultado = cache.get_or_revalidate(
            "k", fetch=lambda: Fetched("fallback", {}), validators=[validador]
        )
        assert resultado.outcome is CacheOutcome.UPDATED
        assert resultado.value == "novo"

    def test_desconhecido_faz_aquisicao_completa(self, tmp_path):
        clock = _Clock()
        cache = _cache(tmp_path, clock)
        cache.get_or_revalidate("k", fetch=lambda: Fetched("antigo", {}))
        clock.avancar(timedelta(hours=2))
        validador = _FixedValidator(RevalidationResult(RevalidationStatus.UNKNOWN))
        chamadas = []

        def fetch() -> Fetched:
            chamadas.append(1)
            return Fetched("completo", {})

        resultado = cache.get_or_revalidate(
            "k", fetch=fetch, validators=[validador]
        )
        assert resultado.outcome is CacheOutcome.UPDATED
        assert resultado.value == "completo"
        assert len(chamadas) == 1

    def test_desconhecido_com_falha_serve_cache(self, tmp_path):
        clock = _Clock()
        cache = _cache(tmp_path, clock)
        cache.get_or_revalidate("k", fetch=lambda: Fetched("antigo", {}))
        clock.avancar(timedelta(hours=2))
        validador = _FixedValidator(RevalidationResult(RevalidationStatus.UNKNOWN))

        def fetch() -> Fetched:
            raise RuntimeError("rede fora")

        resultado = cache.get_or_revalidate(
            "k", fetch=fetch, validators=[validador]
        )
        assert resultado.outcome is CacheOutcome.HIT
        assert resultado.value == "antigo"

    def test_coalescencia_evita_checagem_remota(self, tmp_path):
        clock = _Clock()
        cache = _cache(tmp_path, clock)
        cache.get_or_revalidate("k", fetch=lambda: Fetched("antigo", {}))
        clock.avancar(timedelta(minutes=30))
        validador = _FixedValidator(
            RevalidationResult(RevalidationStatus.CHANGED, payload="novo")
        )
        resultado = cache.get_or_revalidate(
            "k",
            fetch=lambda: Fetched("fallback", {}),
            validators=[validador],
            revalidate_after=timedelta(hours=1),
        )
        assert resultado.outcome is CacheOutcome.HIT
        assert resultado.value == "antigo"
        assert validador.chamadas == 0

    def test_ttl_de_seguranca_forca_aquisicao_completa(self, tmp_path):
        clock = _Clock()
        cache = _cache(tmp_path, clock)
        cache.get_or_revalidate("k", fetch=lambda: Fetched("antigo", {}))
        clock.avancar(timedelta(days=2))
        validador = _FixedValidator(
            RevalidationResult(RevalidationStatus.UNCHANGED)
        )
        resultado = cache.get_or_revalidate(
            "k",
            fetch=lambda: Fetched("renovado", {}),
            validators=[validador],
            safety_ttl=timedelta(hours=24),
        )
        assert resultado.outcome is CacheOutcome.UPDATED
        assert resultado.value == "renovado"
        assert validador.chamadas == 0

    def test_force_refresh_ignora_cache(self, tmp_path):
        clock = _Clock()
        cache = _cache(tmp_path, clock)
        cache.get_or_revalidate("k", fetch=lambda: Fetched("antigo", {}))
        resultado = cache.get_or_revalidate(
            "k", fetch=lambda: Fetched("novo", {}), force_refresh=True
        )
        assert resultado.outcome is CacheOutcome.UPDATED
        assert resultado.value == "novo"

    def test_versao_de_parser_diferente_invalida(self, tmp_path):
        clock = _Clock()
        cache = _cache(tmp_path, clock)
        cache.get_or_revalidate(
            "k", fetch=lambda: Fetched("v1", {}), parser_version="p1"
        )
        resultado = cache.get_or_revalidate(
            "k", fetch=lambda: Fetched("v2", {}), parser_version="p2"
        )
        assert resultado.outcome is CacheOutcome.MISS
        assert resultado.value == "v2"

    def test_retencao_excedida_remove_registro(self, tmp_path):
        clock = _Clock()
        cache = _cache(tmp_path, clock)
        cache.get_or_revalidate("k", fetch=lambda: Fetched("antigo", {}))
        clock.avancar(timedelta(days=40))
        resultado = cache.get_or_revalidate(
            "k", fetch=lambda: Fetched("novo", {}), retention=timedelta(days=30)
        )
        assert resultado.outcome is CacheOutcome.MISS
        assert resultado.value == "novo"

    def test_registro_corrompido_e_miss(self, tmp_path):
        clock = _Clock()
        cache = _cache(tmp_path, clock)
        (tmp_path / "k.json").write_text("not-json", encoding="utf-8")
        resultado = cache.get_or_revalidate("k", fetch=lambda: Fetched("novo", {}))
        assert resultado.outcome is CacheOutcome.MISS

    def test_escrita_usa_tmp_e_rename(self, tmp_path):
        clock = _Clock()
        cache = _cache(tmp_path, clock)
        cache.get_or_revalidate("k", fetch=lambda: Fetched("conteudo", {}))
        assert not list(tmp_path.glob("*.tmp"))
        dados = json.loads((tmp_path / "k.json").read_text(encoding="utf-8"))
        assert dados["payload"] == "conteudo"
        assert REVALIDATED_AT in dados["validators"]


class TestHttpValidator:
    def test_sem_validadores_retorna_unknown(self):
        fetcher = _Fetcher([_Response()])
        validador = HttpValidator(fetcher)
        resultado = validador.revalidate(CacheRecord(payload="x"))
        assert resultado.status is RevalidationStatus.UNKNOWN
        assert fetcher.chamadas == 0

    def test_304_inalterado(self):
        fetcher = _Fetcher([_Response(status=304)])
        validador = HttpValidator(fetcher)
        resultado = validador.revalidate(
            CacheRecord(payload="x", validators={ETAG: "v1"})
        )
        assert resultado.status is RevalidationStatus.UNCHANGED

    def test_200_alterado(self):
        fetcher = _Fetcher([_Response(text="novo", status=200)])
        validador = HttpValidator(fetcher)
        resultado = validador.revalidate(
            CacheRecord(payload="x", validators={ETAG: "v1"})
        )
        assert resultado.status is RevalidationStatus.CHANGED
        assert resultado.payload == "novo"

    def test_falha_retorna_unknown(self):
        fetcher = _Fetcher(RuntimeError("rede"))
        validador = HttpValidator(fetcher)
        resultado = validador.revalidate(
            CacheRecord(payload="x", validators={ETAG: "v1"})
        )
        assert resultado.status is RevalidationStatus.UNKNOWN


class TestDateValidator:
    def _validador(self, resposta):
        return DateValidator(
            _Fetcher([resposta]), lambda html: date.fromisoformat(html)
        )

    def test_data_nao_avancou_inalterado(self):
        resultado = self._validador(_Response("2026-09-09")).revalidate(
            CacheRecord(
                payload="x",
                validators={DATA_ULTIMA_COTACAO: "2026-09-09"},
            )
        )
        assert resultado.status is RevalidationStatus.UNCHANGED

    def test_data_nova_alterado(self):
        resultado = self._validador(_Response("2026-09-10")).revalidate(
            CacheRecord(
                payload="x",
                validators={DATA_ULTIMA_COTACAO: "2026-09-09"},
            )
        )
        assert resultado.status is RevalidationStatus.CHANGED
        assert resultado.payload == "2026-09-10"

    def test_304_inalterado(self):
        resultado = self._validador(_Response(status=304)).revalidate(
            CacheRecord(payload="x", validators={DATA_ULTIMA_COTACAO: "2026-09-09"})
        )
        assert resultado.status is RevalidationStatus.UNCHANGED

    def test_data_ausente_unknown(self):
        resultado = DateValidator(
            _Fetcher([_Response("invalida")]), lambda _html: None
        ).revalidate(CacheRecord(payload="x", validators={DATA_ULTIMA_COTACAO: "2026-09-09"}))
        assert resultado.status is RevalidationStatus.UNKNOWN


class TestFileOrRevalidate:
    def _fetch(self, data: bytes, contador: list):
        def _inner():
            contador.append(1)
            return data, {}

        return _inner

    def test_arquivo_ausente_baixa(self, tmp_path):
        clock = _Clock()
        cache = _cache(tmp_path, clock)
        contador: list = []
        resultado = cache.get_file_or_revalidate(
            tmp_path / "a.zip", fetch=self._fetch(b"dados", contador)
        )
        assert resultado.outcome is CacheOutcome.MISS
        assert resultado.data == b"dados"
        assert (tmp_path / "a.zip").read_bytes() == b"dados"

    def test_probe_ausente_reutiliza_local(self, tmp_path):
        clock = _Clock()
        cache = _cache(tmp_path, clock)
        contador: list = []
        (tmp_path / "a.zip").write_bytes(b"local")
        resultado = cache.get_file_or_revalidate(
            tmp_path / "a.zip", fetch=self._fetch(b"novo", contador)
        )
        assert resultado.outcome is CacheOutcome.HIT
        assert resultado.data == b"local"
        assert contador == []

    def test_probe_inalterado_revalida(self, tmp_path):
        clock = _Clock()
        cache = _cache(tmp_path, clock)
        (tmp_path / "a.zip").write_bytes(b"local")
        probe = lambda _v: RevalidationResult(
            RevalidationStatus.UNCHANGED, validators={ETAG: "v2"}
        )
        resultado = cache.get_file_or_revalidate(
            tmp_path / "a.zip", fetch=self._fetch(b"novo", []), probe=probe
        )
        assert resultado.outcome is CacheOutcome.REVALIDATED
        assert resultado.data == b"local"

    def test_probe_alterado_rebaixa(self, tmp_path):
        clock = _Clock()
        cache = _cache(tmp_path, clock)
        (tmp_path / "a.zip").write_bytes(b"local")
        contador: list = []
        probe = lambda _v: RevalidationResult(RevalidationStatus.CHANGED)
        resultado = cache.get_file_or_revalidate(
            tmp_path / "a.zip",
            fetch=self._fetch(b"novo", contador),
            probe=probe,
        )
        assert resultado.outcome is CacheOutcome.UPDATED
        assert resultado.data == b"novo"
        assert contador == [1]

    def test_probe_falha_serve_local(self, tmp_path):
        clock = _Clock()
        cache = _cache(tmp_path, clock)
        (tmp_path / "a.zip").write_bytes(b"local")

        def probe(_v):
            raise RuntimeError("rede")

        resultado = cache.get_file_or_revalidate(
            tmp_path / "a.zip", fetch=self._fetch(b"novo", []), probe=probe
        )
        assert resultado.outcome is CacheOutcome.HIT
        assert resultado.data == b"local"

    def test_coalescencia_nao_chama_probe(self, tmp_path):
        clock = _Clock()
        cache = _cache(tmp_path, clock)
        (tmp_path / "a.zip").write_bytes(b"local")
        chamadas: list = []
        metadata: dict = {}

        def probe(_v):
            chamadas.append(1)
            return RevalidationResult(RevalidationStatus.CHANGED)

        def read_validators():
            return metadata

        def write_metadata(data, validators, _agora):
            metadata.update(validators)
            metadata[REVALIDATED_AT] = clock().isoformat()

        cache.get_file_or_revalidate(
            tmp_path / "a.zip",
            fetch=self._fetch(b"v2", []),
            probe=probe,
            revalidate_after=timedelta(hours=6),
            read_validators=read_validators,
            write_metadata=write_metadata,
        )
        resultado = cache.get_file_or_revalidate(
            tmp_path / "a.zip",
            fetch=self._fetch(b"v3", []),
            probe=probe,
            revalidate_after=timedelta(hours=6),
            read_validators=read_validators,
            write_metadata=write_metadata,
        )
        assert resultado.outcome is CacheOutcome.HIT
        assert chamadas == [1]
