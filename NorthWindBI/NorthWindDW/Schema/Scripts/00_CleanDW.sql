PRINT 'Limpiando tablas de NorthWindDW...';
SET NOCOUNT ON;

DELETE FROM [dbo].[FactSales];
DELETE FROM [dbo].[DimProduct];
DELETE FROM [dbo].[DimEmployee];
DELETE FROM [dbo].[DimCustomer];
DELETE FROM [dbo].[DimShipper];
DELETE FROM [dbo].[DimDate];

PRINT 'Limpieza de NorthWindDW completada.';
GO
