"""Modelo puro do formulário de configuração de LLM (sem Tk).

Concentra a carga da configuração salva, a troca de provedor (guardando o
formulário em memória), a resolução de presets e a coleta dos valores. O
diálogo apenas liga ``StringVar`` a este modelo, de modo que a lógica seja
verificável sem ``DISPLAY``.
"""

from pathlib import Path

from flowscope.application.llm_config_port import LLMConfigPort

#: RPM assumido quando o campo informado não é um inteiro válido.
_RPM_PADRAO = 5


class LLMConfigForm:
    """Estado e transições do formulário de configuração de LLM."""

    def __init__(
        self: "LLMConfigForm",
        port: LLMConfigPort,
        config_path: Path | None = None,
    ) -> None:
        """Inicializa o modelo com os presets e os defaults do provedor."""
        self._port = port
        self._config_path = config_path
        self._presets = port.get_presets()
        self._working: dict[str, dict] = {}
        self._provider_atual = "none"
        self.provider = "none"
        self.api_url = ""
        self.model = ""
        self.api_key = ""
        self.rpm = str(port.default_config()["rpm"])

    @property
    def presets(self: "LLMConfigForm") -> list[str]:
        """Retorna os nomes dos provedores disponíveis como presets."""
        return list(self._presets)

    def carregar_inicial(self: "LLMConfigForm") -> None:
        """Carrega a configuração salva do provedor ativo."""
        self._working = self._port.load_provider_configs(self._config_path)
        config = self._port.load_llm_config(self._config_path)
        self._provider_atual = config["provider"]
        self._aplicar_campos(
            config["provider"],
            config["api_url"],
            config["model"],
            config["api_key"],
            str(config["rpm"]),
        )

    def trocar_provider(self: "LLMConfigForm", provider: str) -> None:
        """Guarda o provedor atual e exibe a config do novo provedor."""
        self._descarregar_provedor_atual()
        self._provider_atual = provider
        self.provider = provider
        self._carregar_provedor(provider)

    def coletar_campos_provedor(self: "LLMConfigForm") -> dict:
        """Monta os campos do provedor a partir do formulário atual."""
        return {
            "api_url": self.api_url.strip(),
            "model": self.model.strip(),
            "api_key": self.api_key.strip(),
            "rpm": self.rpm_int(),
        }

    def coletar_config(self: "LLMConfigForm") -> dict:
        """Monta a configuração a partir dos valores atualmente preenchidos."""
        return {
            "provider": self.provider,
            "api_url": self.api_url.strip(),
            "model": self.model.strip(),
            "api_key": self.api_key.strip(),
            "rpm": self.rpm_int(),
        }

    def rpm_int(self: "LLMConfigForm") -> int:
        """Retorna o RPM informado, caindo no padrão quando inválido."""
        try:
            return int(self.rpm)
        except (TypeError, ValueError):
            return _RPM_PADRAO

    def _descarregar_provedor_atual(self: "LLMConfigForm") -> None:
        """Guarda o formulário atual em memória para o provedor ativo."""
        if self._provider_atual == "none":
            return
        self._working[self._provider_atual] = self.coletar_campos_provedor()

    def _carregar_provedor(self: "LLMConfigForm", provider: str) -> None:
        """Exibe a configuração salva do provedor ou os defaults do preset."""
        rpm_padrao = str(self._port.default_config()["rpm"])
        if provider == "none":
            self._aplicar_campos("none", "", "", "", rpm_padrao)
            return
        entrada = self._working.get(provider)
        if entrada is not None:
            self._aplicar_campos(
                provider,
                str(entrada["api_url"]),
                str(entrada["model"]),
                str(entrada["api_key"]),
                str(entrada["rpm"]),
            )
            return
        preset = self._presets.get(provider)
        self._aplicar_campos(
            provider,
            str(preset["api_url"]) if preset else "",
            str(preset["model"]) if preset else "",
            "",
            rpm_padrao,
        )

    def _aplicar_campos(
        self: "LLMConfigForm",
        provider: str,
        api_url: object,
        model: object,
        api_key: object,
        rpm: str,
    ) -> None:
        """Escreve os valores dos campos no modelo."""
        self.provider = provider
        self.api_url = str(api_url)
        self.model = str(model)
        self.api_key = str(api_key)
        self.rpm = rpm
