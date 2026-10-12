/*
Script de Post-Deployment - Carga inicial del Data Warehouse
Base de datos origen: NorthWindOLTP
*/

PRINT '========================================';
PRINT 'Iniciando carga del Data Warehouse...';
PRINT 'Origen: NorthWindOLTP';
PRINT '========================================';

:r .\01_Load_DimCustomer.sql
:r .\02_Load_DimEmployee.sql
:r .\03_Load_DimProduct.sql
:r .\04_Load_DimShipper.sql
:r .\05_Load_DimDate.sql
:r .\06_Load_FactSales.sql

PRINT '========================================';
PRINT 'Carga del Data Warehouse completada.';
PRINT '========================================';