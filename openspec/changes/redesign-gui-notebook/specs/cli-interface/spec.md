## REMOVED Requirements

### Requirement: Exportação CSV de CVD via --cvd

**Reason**: O gráfico CVD foi removido da interface gráfica e o caso de uso ExportCVDUseCase foi eliminado. Manter a exportação via CLI para um indicador sem representação visual geraria confusão. Uma futura funcionalidade genérica de exportação de dados brutos poderá substituí-la.
**Migration**: Usar a flag `--vwap` para exportação VWAP, ou a interface gráfica para copiar dados via botão "Copiar Dados".
