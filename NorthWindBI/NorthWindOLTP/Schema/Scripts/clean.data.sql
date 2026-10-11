/* Borra los datos en orden inverso a las dependencias FK,
   para que el deploy pueda ejecutarse varias veces sin duplicados. */
PRINT 'Limpiando datos existentes...';
SET NOCOUNT ON;
DELETE FROM [dbo].[OrderDetails];
DELETE FROM [dbo].[Orders];
DELETE FROM [dbo].[Products];
DELETE FROM [dbo].[CustomerCustomerDemo];
DELETE FROM [dbo].[CustomerDemographics];
DELETE FROM [dbo].[Customers];
DELETE FROM [dbo].[EmployeeTerritories];
DELETE FROM [dbo].[Employees];
DELETE FROM [dbo].[Territories];
DELETE FROM [dbo].[Region];
DELETE FROM [dbo].[Suppliers];
DELETE FROM [dbo].[Categories];
DELETE FROM [dbo].[Shippers];