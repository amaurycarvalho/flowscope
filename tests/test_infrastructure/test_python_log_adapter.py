import logging
from unittest.mock import MagicMock

from flowscope.application.logging_port import LogEntry, LogReference
from flowscope.infrastructure.logging.python_log_adapter import PythonLogAdapter


class TestPythonLogAdapter:
    def test_error_loga_com_nivel_error(self):
        logger = MagicMock()
        adapter = PythonLogAdapter(logger)
        entry = LogEntry("mensagem", "ERROR", "Modulo")

        ref = adapter.error(entry)

        logger.log.assert_called_once()
        args = logger.log.call_args
        assert args[0][0] == logging.ERROR
        assert "[Modulo] mensagem" in args[0][1]
        assert isinstance(ref, LogReference)
        assert ref.source == "flowscope.log"

    def test_warning_loga_com_nivel_warning(self):
        logger = MagicMock()
        adapter = PythonLogAdapter(logger)
        entry = LogEntry("aviso", "WARNING", "Modulo")

        ref = adapter.warning(entry)

        logger.log.assert_called_once()
        assert logger.log.call_args[0][0] == logging.WARNING
        assert isinstance(ref, LogReference)

    def test_info_loga_com_nivel_info(self):
        logger = MagicMock()
        adapter = PythonLogAdapter(logger)
        entry = LogEntry("informativo", "INFO", "Modulo")

        ref = adapter.info(entry)

        logger.log.assert_called_once()
        assert logger.log.call_args[0][0] == logging.INFO
        assert isinstance(ref, LogReference)

    def test_error_com_exception_inclui_stack_trace(self):
        logger = MagicMock()
        adapter = PythonLogAdapter(logger)
        try:
            raise ValueError("algo deu errado")
        except ValueError as exc:
            entry = LogEntry("msg", "ERROR", "Modulo", exception=exc)

        adapter.error(entry)

        args = logger.log.call_args[0]
        assert "ValueError: algo deu errado" in args[1]
        assert "Traceback" in args[1]

    def test_log_nos_handlers_reais(self):
        log = logging.getLogger("test_flowscope")
        log.setLevel(logging.WARNING)
        handler = logging.StreamHandler(__import__("io").StringIO())
        handler.setLevel(logging.WARNING)
        log.handlers.clear()
        log.addHandler(handler)

        adapter = PythonLogAdapter(log)
        entry = LogEntry("teste real", "ERROR", "Modulo")

        ref = adapter.error(entry)

        output = handler.stream.getvalue()
        assert "[Modulo] teste real" in output
        assert isinstance(ref, LogReference)
