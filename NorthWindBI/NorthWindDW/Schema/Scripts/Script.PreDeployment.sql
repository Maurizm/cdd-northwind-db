/*
=============================================================================
Script Pre-Deployment: Limpieza previa de NorthWindDW
=============================================================================
Vacía las tablas ANTES de los cambios de esquema para que los ALTER TABLE
con columnas NOT NULL no fallen sobre tablas con datos.
Los datos se recargan en el post-deployment (00_CleanDW + loads).
Los OBJECT_ID permiten correrlo en el primer deploy (objetos aún no existen).
=============================================================================
*/
PRINT 'Pre-Deployment: limpiando datos existentes de NorthWindDW...';
SET NOCOUNT ON;

-- Hecho primero (origen de FKs)
IF OBJECT_ID(N'[dbo].[FactSales]', N'U') IS NOT NULL
    DELETE FROM [dbo].[FactSales];

-- Dimensiones
IF OBJECT_ID(N'[dbo].[DimProduct]', N'U') IS NOT NULL
    DELETE FROM [dbo].[DimProduct];
IF OBJECT_ID(N'[dbo].[DimSupplier]', N'U') IS NOT NULL
    DELETE FROM [dbo].[DimSupplier];
IF OBJECT_ID(N'[dbo].[DimEmployee]', N'U') IS NOT NULL
    DELETE FROM [dbo].[DimEmployee];
IF OBJECT_ID(N'[dbo].[DimCustomer]', N'U') IS NOT NULL
    DELETE FROM [dbo].[DimCustomer];
IF OBJECT_ID(N'[dbo].[DimShipper]', N'U') IS NOT NULL
    DELETE FROM [dbo].[DimShipper];
IF OBJECT_ID(N'[dbo].[DimGeography]', N'U') IS NOT NULL
    DELETE FROM [dbo].[DimGeography];
IF OBJECT_ID(N'[dbo].[DimDate]', N'U') IS NOT NULL
    DELETE FROM [dbo].[DimDate];

-- Staging
IF OBJECT_ID(N'[staging].[customer]', N'U') IS NOT NULL
    TRUNCATE TABLE [staging].[customer];
IF OBJECT_ID(N'[staging].[employee]', N'U') IS NOT NULL
    TRUNCATE TABLE [staging].[employee];
IF OBJECT_ID(N'[staging].[product]', N'U') IS NOT NULL
    TRUNCATE TABLE [staging].[product];
IF OBJECT_ID(N'[staging].[supplier]', N'U') IS NOT NULL
    TRUNCATE TABLE [staging].[supplier];
IF OBJECT_ID(N'[staging].[shipper]', N'U') IS NOT NULL
    TRUNCATE TABLE [staging].[shipper];
IF OBJECT_ID(N'[staging].[sales]', N'U') IS NOT NULL
    TRUNCATE TABLE [staging].[sales];

PRINT 'Pre-Deployment completado.';
GO
