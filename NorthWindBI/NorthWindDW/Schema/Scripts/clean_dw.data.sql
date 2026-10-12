/* Limpia el DW en orden inverso a las FK para repoblarlo desde cero. */
PRINT 'Limpiando NorthwindDW...';
SET NOCOUNT ON;
DELETE FROM [dbo].[FactSales];
DELETE FROM [dbo].[DimProduct];
DELETE FROM [dbo].[DimEmployee];
DELETE FROM [dbo].[DimCustomer];
DELETE FROM [dbo].[DimShipper];
DELETE FROM [dbo].[DimDate];