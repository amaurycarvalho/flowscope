"""Infraestrutura de LLM: presets, configuração, rate limiter e adaptador."""

import os

#: Variável de ambiente que força o liteLLM a usar o catálogo local de preços.
VARIAVEL_MODEL_COST_MAP_LOCAL = "LITELLM_LOCAL_MODEL_COST_MAP"


def preparar_litellm() -> None:
    """Prepara o liteLLM para usar o catálogo local de model cost map.

    Define ``LITELLM_LOCAL_MODEL_COST_MAP=True`` apenas quando o usuário não
    escolheu um valor, preservando um override explícito (por exemplo ``False``
    para forçar o catálogo remoto). A variável precisa existir antes do primeiro
    ``import litellm``.
    """
    os.environ.setdefault(VARIAVEL_MODEL_COST_MAP_LOCAL, "True")


preparar_litellm()
