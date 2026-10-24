"""Fonte CVM dos títulos de renda fixa: FRE, SECURIT e informes de FII."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import date

from flowscope.application.renda_fixa.resultados import ResultadoFontes
from flowscope.domain.renda_fixa import (
    PARSER_VERSION,
    CarteiraTitulos,
    FonteTitulos,
    TipoTitulo,
    TituloAgregado,
    TituloRendaFixa,
)
from flowscope.infrastructure.cvm import renda_fixa_carga as carga
from flowscope.infrastructure.cvm.datasets import CvmDatasetDownloader, hash_sha256
from flowscope.infrastructure.cvm.renda_fixa_fii import FONTE_TRIMESTRAL
from flowscope.infrastructure.cvm.renda_fixa_join import (
    enriquecer,
    indice_securit,
)

logger = logging.getLogger("flowscope")

#: Diretórios oficiais dos datasets usados na renda fixa.
FRE_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FRE/DADOS"
SECURIT_CRI_URL = (
    "https://dados.cvm.gov.br/dados/SECURIT/DOC/INF_MENSAL_CRI/DADOS"
)
SECURIT_CRA_URL = (
    "https://dados.cvm.gov.br/dados/SECURIT/DOC/INF_MENSAL_CRA/DADOS"
)
FII_TRIMESTRAL_URL = (
    "https://dados.cvm.gov.br/dados/FII/DOC/INF_TRIMESTRAL/DADOS"
)
FII_MENSAL_URL = "https://dados.cvm.gov.br/dados/FII/DOC/INF_MENSAL/DADOS"

#: Quantidade de anos consultados para trás a partir da referência.
_ANOS_JANELA = 2


class CvmTitulosSource:
    """Baixa e normaliza os datasets CVM, tolerando falha isolada por fonte."""

    def __init__(
        self: CvmTitulosSource,
        downloader_fre: CvmDatasetDownloader | None = None,
        downloader_cri: CvmDatasetDownloader | None = None,
        downloader_cra: CvmDatasetDownloader | None = None,
        downloader_fii: CvmDatasetDownloader | None = None,
        downloader_fii_mensal: CvmDatasetDownloader | None = None,
        anos_janela: int = _ANOS_JANELA,
        enriquecer_securit: bool = True,
    ) -> None:
        """Monta os downloaders padrão quando não injetados."""
        self._fre = downloader_fre or _downloader_fre()
        self._cri = downloader_cri or _downloader_cri()
        self._cra = downloader_cra or _downloader_cra()
        self._fii = downloader_fii or _downloader_fii()
        self._fii_mensal = downloader_fii_mensal or _downloader_fii_mensal()
        self._anos_janela = anos_janela
        self._enriquecer_securit = enriquecer_securit

    def obter(
        self: CvmTitulosSource,
        ticker: str,
        cnpj: str,
        tipo_ativo: str,
        reference_date: date,
        progress: Callable[[int, int, str], None] | None = None,
        cancelar: Callable[[], None] | None = None,
        anterior: CarteiraTitulos | None = None,
    ) -> ResultadoFontes:
        """Obtém e normaliza as obrigações e direitos do ticker."""
        carga.checar(cancelar)
        anos = carga.anos(reference_date, self._anos_janela)
        if anterior is not None and self._reutilizavel(anterior, tipo_ativo, anos):
            return _resultado_do_cache(anterior)
        fontes: dict[str, FonteTitulos] = {}
        falhas: set[str] = set()
        obrigacoes: list[TituloRendaFixa] = []
        direitos: list[TituloRendaFixa] = []
        agregados: list[TituloAgregado] = []
        total = 5 if tipo_ativo == "fii" else 3
        atual = 0
        if tipo_ativo != "fii":
            atual = self._obter_fre(
                cnpj,
                anos,
                obrigacoes,
                fontes,
                falhas,
                progress,
                atual,
                total,
                cancelar,
            )
        else:
            atual = self._obter_fii(
                ticker,
                cnpj,
                anos,
                direitos,
                agregados,
                fontes,
                falhas,
                progress,
                atual,
                total,
                cancelar,
            )
        indices = self._obter_securit(
            anos,
            fontes,
            falhas,
            progress,
            atual,
            total,
            obrigacoes,
            direitos,
            cancelar,
        )
        if indices:
            obrigacoes[:] = [enriquecer(item, indices) for item in obrigacoes]
            direitos[:] = [enriquecer(item, indices) for item in direitos]
        carga.checar(cancelar)
        return ResultadoFontes(
            obrigacoes=tuple(carga.deduplicar(obrigacoes)),
            direitos=tuple(carga.deduplicar(direitos)),
            agregados=tuple(carga.deduplicar_agregados(agregados)),
            fontes=fontes,
            falhas=frozenset(falhas),
        )

    def _reutilizavel(
        self: CvmTitulosSource,
        anterior: CarteiraTitulos,
        tipo_ativo: str,
        anos: list[int],
    ) -> bool:
        """Indica se os datasets de origem continuam iguais ao cache anterior."""
        if anterior.parser_version != PARSER_VERSION:
            return False
        fontes = self._fontes_necessarias(anterior, tipo_ativo)
        if not fontes:
            return False
        for chave, downloader in fontes.items():
            registro = anterior.fontes.get(chave)
            if registro is None or not registro.hash:
                return False
            try:
                atual = _assinatura_anos(downloader, anos)
            except Exception:  # falha de leitura/revalidação força a reaquisição
                return False
            if atual != registro.hash:
                return False
        return True

    def _fontes_necessarias(
        self: CvmTitulosSource,
        anterior: CarteiraTitulos,
        tipo_ativo: str,
    ) -> dict[str, CvmDatasetDownloader]:
        """Lista os datasets cuja assinatura precisa ser conferida no cache."""
        if tipo_ativo == "fii":
            fontes: dict[str, CvmDatasetDownloader] = {
                "fii_ativo": self._fii,
                "fii_mensal": self._fii_mensal,
            }
        else:
            fontes = {"fre": self._fre}
        if not self._enriquecer_securit:
            return {}
        tipos = {item.tipo for item in (*anterior.obrigacoes, *anterior.direitos)}
        if TipoTitulo.CRI in tipos:
            fontes["securit_cri"] = self._cri
        if TipoTitulo.CRA in tipos:
            fontes["securit_cra"] = self._cra
        return fontes

    def _obter_fre(
        self: CvmTitulosSource,
        cnpj: str,
        anos: list[int],
        destino: list[TituloRendaFixa],
        fontes: dict[str, FonteTitulos],
        falhas: set[str],
        progress: Callable[[int, int, str], None] | None,
        atual: int,
        total: int,
        cancelar: Callable[[], None] | None = None,
    ) -> int:
        """Carrega o FRE e acumula as obrigações."""
        carga.reportar(progress, atual, total, "Títulos: FRE")
        carga.checar(cancelar)
        try:
            destino.extend(
                carga.carregar_fre(self._fre, cnpj, anos, fontes, cancelar)
            )
        except Exception:  # falha isolada da fonte FRE
            logger.warning("Falha ao adquirir FRE de renda fixa", exc_info=True)
            falhas.add("FRE")
        return atual + 1

    def _obter_fii(
        self: CvmTitulosSource,
        ticker: str,
        cnpj: str,
        anos: list[int],
        direitos: list[TituloRendaFixa],
        agregados: list[TituloAgregado],
        fontes: dict[str, FonteTitulos],
        falhas: set[str],
        progress: Callable[[int, int, str], None] | None,
        atual: int,
        total: int,
        cancelar: Callable[[], None] | None = None,
    ) -> int:
        """Carrega os informes trimestral e mensal do FII."""
        carga.reportar(progress, atual, total, "Títulos: carteira do FII")
        carga.checar(cancelar)
        try:
            direitos.extend(
                carga.carregar_fii_ativo(
                    self._fii, cnpj, anos, fontes, cancelar
                )
            )
        except Exception:  # falha isolada da carteira
            logger.warning(
                "Falha ao adquirir carteira do FII %s", ticker, exc_info=True
            )
            falhas.add(FONTE_TRIMESTRAL)
        atual += 1
        carga.reportar(progress, atual, total, "Títulos: agregados do FII")
        carga.checar(cancelar)
        try:
            agregados.extend(
                carga.carregar_fii_passivo(
                    self._fii_mensal, cnpj, anos, fontes, cancelar
                )
            )
        except Exception:  # falha isolada dos agregados
            logger.warning(
                "Falha ao adquirir agregados do FII %s", ticker, exc_info=True
            )
            falhas.add("FII_INF_MENSAL")
        return atual + 1

    def _obter_securit(
        self: CvmTitulosSource,
        anos: list[int],
        fontes: dict[str, FonteTitulos],
        falhas: set[str],
        progress: Callable[[int, int, str], None] | None,
        atual: int,
        total: int,
        obrigacoes: list[TituloRendaFixa],
        direitos: list[TituloRendaFixa],
        cancelar: Callable[[], None] | None = None,
    ) -> dict[str, TituloRendaFixa]:
        """Carrega CRI/CRA apenas para os títulos ligados ao ticker."""
        if not self._enriquecer_securit:
            return {}
        codigos, cnpjs = carga.alvos_join(obrigacoes, direitos)
        if not codigos and not cnpjs:
            return {}
        indice: dict[str, TituloRendaFixa] = {}
        for tipo, downloader, fonte, nome, posicao in (
            (TipoTitulo.CRI, self._cri, "SECURIT_CRI", "Títulos: CRI", atual),
            (TipoTitulo.CRA, self._cra, "SECURIT_CRA", "Títulos: CRA", atual + 1),
        ):
            carga.reportar(progress, posicao, total, nome)
            carga.checar(cancelar)
            try:
                itens = carga.carregar_securit(
                    downloader,
                    tipo,
                    anos,
                    fonte.lower(),
                    fontes,
                    codigos,
                    cnpjs,
                    cancelar,
                )
            except Exception:  # falha isolada do SECURIT
                logger.warning(
                    "Falha ao adquirir SECURIT %s", tipo.rotulo, exc_info=True
                )
                falhas.add(fonte)
                continue
            indice.update(indice_securit(itens))
        return indice


def _assinatura_anos(downloader: CvmDatasetDownloader, anos: list[int]) -> str:
    """Retorna a assinatura dos arquivos anuais, sem extrair os CSVs."""
    digests = [hash_sha256(downloader.baixar_ano(ano)) for ano in anos]
    return "; ".join(dict.fromkeys(digests))


def _resultado_do_cache(anterior: CarteiraTitulos) -> ResultadoFontes:
    """Reaproveita os dados normalizados quando nenhum dataset mudou."""
    return ResultadoFontes(
        obrigacoes=anterior.obrigacoes,
        direitos=anterior.direitos,
        agregados=anterior.agregados,
        fontes=dict(anterior.fontes),
        falhas=frozenset(),
    )


def _downloader(
    url: str, arquivo: str, dataset: str
) -> CvmDatasetDownloader:
    """Cria um downloader anual para o dataset informado."""
    return CvmDatasetDownloader(
        base_url=url,
        arquivo=lambda ano: f"{arquivo}_{ano}.zip",
        dataset=dataset,
        parser_version=PARSER_VERSION,
    )


def _downloader_fre() -> CvmDatasetDownloader:
    """Cria o downloader do FRE."""
    return _downloader(FRE_URL, "fre_cia_aberta", "fre")


def _downloader_cri() -> CvmDatasetDownloader:
    """Cria o downloader do Informe Mensal de CRI."""
    return _downloader(
        SECURIT_CRI_URL, "inf_mensal_cri", "securit-cri-renda-fixa"
    )


def _downloader_cra() -> CvmDatasetDownloader:
    """Cria o downloader do Informe Mensal de CRA."""
    return _downloader(
        SECURIT_CRA_URL, "inf_mensal_cra", "securit-cra-renda-fixa"
    )


def _downloader_fii() -> CvmDatasetDownloader:
    """Cria o downloader do Informe Trimestral de FII."""
    return _downloader(
        FII_TRIMESTRAL_URL, "inf_trimestral_fii", "FII-INF-TRIMESTRAL"
    )


def _downloader_fii_mensal() -> CvmDatasetDownloader:
    """Cria o downloader do Informe Mensal de FII."""
    return _downloader(
        FII_MENSAL_URL, "inf_mensal_fii", "inf_mensal"
    )
