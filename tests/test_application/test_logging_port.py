from datetime import datetime

from flowscope.application.logging_port import LogEntry, LogReference, LogPort


class TestLogEntry:
    def test_define_timestamp_automatico(self):
        entry = LogEntry(message="erro", level="ERROR", component="Test")
        assert entry.message == "erro"
        assert entry.level == "ERROR"
        assert entry.component == "Test"
        assert entry.exception is None
        assert entry.context is None
        assert isinstance(entry.timestamp, datetime)

    def test_campos_opcionais_sao_preenchidos(self):
        exc = ValueError("bug")
        entry = LogEntry(
            message="falha",
            level="ERROR",
            component="Test",
            exception=exc,
            context={"key": "val"},
        )
        assert entry.exception is exc
        assert entry.context == {"key": "val"}


class TestLogReference:
    def test_campos_sao_armazenados(self):
        ref = LogReference(
            source="syslog",
            identifier="2026-07-09T12:00:00",
            hint="Consulte o log",
        )
        assert ref.source == "syslog"
        assert ref.identifier == "2026-07-09T12:00:00"
        assert ref.hint == "Consulte o log"

    def test_imutavel(self):
        ref = LogReference(source="a", identifier="b", hint="c")
        with __import__("pytest").raises(AttributeError):
            ref.source = "outro"


class TestLogPort:
    def test_protocolo_aceita_adapter(self):
        class FakeLogger:
            def error(self, entry: LogEntry) -> LogReference:
                return LogReference(source="test", identifier="1", hint="hint")

            def warning(self, entry: LogEntry) -> LogReference:
                return LogReference(source="test", identifier="1", hint="hint")

            def info(self, entry: LogEntry) -> LogReference:
                return LogReference(source="test", identifier="1", hint="hint")

        logger: LogPort = FakeLogger()
        ref = logger.error(LogEntry("msg", "ERROR", "Test"))
        assert ref.source == "test"
