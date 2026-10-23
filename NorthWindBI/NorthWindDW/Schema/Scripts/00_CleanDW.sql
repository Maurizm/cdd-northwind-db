PRINT 'Limpiando tablas de NorthWindDW...';
SET NOCOUNT ON;

DELETE FROM [dbo].[FactSales];
DELETE FROM [dbo].[DimProduct];
DELETE FROM [dbo].[DimSupplier];
DELETE FROM [dbo].[DimEmployee];
DELETE FROM [dbo].[DimCustomer];
DELETE FROM [dbo].[DimShipper];
DELETE FROM [dbo].[DimGeography];
DELETE FROM [dbo].[DimDate];

TRUNCATE TABLE [staging].[customer];
TRUNCATE TABLE [staging].[employee];
TRUNCATE TABLE [staging].[product];
TRUNCATE TABLE [staging].[supplier];
TRUNCATE TABLE [staging].[shipper];
TRUNCATE TABLE [staging].[sales];

-- Resetear watermarks: limpieza = recarga completa
UPDATE [dbo].[PackageConfig] SET [LastRowVersion] = 0;

PRINT 'Limpieza de NorthWindDW completada.';
GO
