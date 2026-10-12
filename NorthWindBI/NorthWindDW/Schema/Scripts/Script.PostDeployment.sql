/*
=============================================================================
Script Post-Deployment: Carga y Población de NorthWindDW
Base de datos origen: NorthWindOLTP
=============================================================================
*/

:setvar OLTP_DB "NorthWindOLTP"

PRINT '==================================================';
PRINT 'Iniciando Post-Deployment ETL para NorthWindDW...';
PRINT 'Origen configurado: $(OLTP_DB)';
PRINT '==================================================';

:r .\00_CleanDW.sql
:r .\01_Load_DimDate.sql
:r .\02_Load_Dimensions.sql
:r .\03_Load_FactSales.sql

PRINT '==================================================';
PRINT 'Carga ETL de NorthWindDW completada con éxito.';
PRINT '==================================================';
GO
