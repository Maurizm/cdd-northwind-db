/*
Carga inicial de dimensiones desde NorthWind.
Ejecutar después de crear todas las tablas dimensionales.
Este script es una carga inicial; no reemplaza el proceso ETL incremental SCD tipo 2.
Se presupone que la base fuente se llama NorthWind y sus tablas están en dbo.
*/
USE NorthWindDW;
GO
SET XACT_ABORT ON;
BEGIN TRANSACTION;

-- Cliente: una versión inicial por cliente.
INSERT dbo.DimCustomer
    (CustomerID, CompanyName, ContactName, ContactTitle, Address, City, Region,
     PostalCode, Country, Phone, Fax, ValidFrom, ValidTo, IsCurrent)
SELECT c.CustomerID, c.CompanyName, c.ContactName, c.ContactTitle, c.Address,
       c.City, c.Region, c.PostalCode, c.Country, c.Phone, c.Fax,
       CONVERT(datetime2(0),'19000101'), CONVERT(datetime2(0),'99991231'), 1
FROM NorthWind.dbo.Customers c
WHERE NOT EXISTS
    (SELECT 1 FROM dbo.DimCustomer d WHERE d.CustomerID = c.CustomerID AND d.IsCurrent = 1);

-- Producto, categoría y proveedor quedan integrados en una dimensión desnormalizada.
INSERT dbo.DimProduct
    (ProductID, ProductName, QuantityPerUnit, Discontinued, UnitPriceCurrent,
     CategoryID, CategoryName, CategoryDescription, SupplierID, SupplierName,
     SupplierCity, SupplierRegion, SupplierCountry, ValidFrom, ValidTo, IsCurrent)
SELECT p.ProductID, p.ProductName, p.QuantityPerUnit, p.Discontinued,
       CONVERT(decimal(19,4),p.UnitPrice), p.CategoryID, c.CategoryName, c.Description,
       p.SupplierID, s.CompanyName, s.City, s.Region, s.Country,
       CONVERT(datetime2(0),'19000101'), CONVERT(datetime2(0),'99991231'), 1
FROM NorthWind.dbo.Products p
LEFT JOIN NorthWind.dbo.Categories c ON c.CategoryID = p.CategoryID
LEFT JOIN NorthWind.dbo.Suppliers s ON s.SupplierID = p.SupplierID
WHERE NOT EXISTS
    (SELECT 1 FROM dbo.DimProduct d WHERE d.ProductID = p.ProductID AND d.IsCurrent = 1);

INSERT dbo.DimEmployee
    (EmployeeID, FirstName, LastName, FullName, Title, TitleOfCourtesy, HireDate,
     City, Region, PostalCode, Country, ReportsToEmployeeID, ValidFrom, ValidTo, IsCurrent)
SELECT e.EmployeeID, e.FirstName, e.LastName,
       CONCAT(e.FirstName, N' ', e.LastName), e.Title, e.TitleOfCourtesy,
       CONVERT(date,e.HireDate), e.City, e.Region, e.PostalCode, e.Country, e.ReportsTo,
       CONVERT(datetime2(0),'19000101'), CONVERT(datetime2(0),'99991231'), 1
FROM NorthWind.dbo.Employees e
WHERE NOT EXISTS
    (SELECT 1 FROM dbo.DimEmployee d WHERE d.EmployeeID = e.EmployeeID AND d.IsCurrent = 1);

INSERT dbo.DimShipper(ShipperID, CompanyName, Phone, IsCurrent)
SELECT s.ShipperID, s.CompanyName, s.Phone, 1
FROM NorthWind.dbo.Shippers s
WHERE NOT EXISTS (SELECT 1 FROM dbo.DimShipper d WHERE d.ShipperID = s.ShipperID AND d.IsCurrent = 1);

-- Clave 0 representa fecha desconocida. Crear fechas que aparezcan en Orders.
;WITH SourceDates AS
(
    SELECT CONVERT(date, OrderDate) AS D FROM NorthWind.dbo.Orders WHERE OrderDate IS NOT NULL
    UNION SELECT CONVERT(date, RequiredDate) FROM NorthWind.dbo.Orders WHERE RequiredDate IS NOT NULL
    UNION SELECT CONVERT(date, ShippedDate) FROM NorthWind.dbo.Orders WHERE ShippedDate IS NOT NULL
)
INSERT dbo.DimDate(DateKey, FullDate, [Day], [Month], MonthName, [Quarter], [Year],
                   WeekOfYear, DayOfWeek, DayName, IsWeekend)
SELECT CONVERT(int,CONVERT(char(8),D,112)), D, DATEPART(day,D), DATEPART(month,D),
       DATENAME(month,D), DATEPART(quarter,D), DATEPART(year,D),
       DATEPART(ISO_WEEK,D), DATEPART(weekday,D), DATENAME(weekday,D),
       CASE WHEN (DATEDIFF(day,CONVERT(date,'19000101'),D) % 7) IN (5,6) THEN 1 ELSE 0 END
FROM SourceDates sd
WHERE NOT EXISTS (SELECT 1 FROM dbo.DimDate dd
                  WHERE dd.DateKey = CONVERT(int,CONVERT(char(8),sd.D,112)));

-- Destinos distintos de envío por combinación de campos.
INSERT dbo.DimShipTo(ShipName, ShipAddress, ShipCity, ShipRegion, ShipPostalCode, ShipCountry)
SELECT DISTINCT o.ShipName, o.ShipAddress, o.ShipCity, o.ShipRegion, o.ShipPostalCode, o.ShipCountry
FROM NorthWind.dbo.Orders o
WHERE NOT EXISTS
(
    SELECT 1 FROM dbo.DimShipTo d
    WHERE ISNULL(d.ShipName,N'') = ISNULL(o.ShipName,N'')
      AND ISNULL(d.ShipAddress,N'') = ISNULL(o.ShipAddress,N'')
      AND ISNULL(d.ShipCity,N'') = ISNULL(o.ShipCity,N'')
      AND ISNULL(d.ShipRegion,N'') = ISNULL(o.ShipRegion,N'')
      AND ISNULL(d.ShipPostalCode,N'') = ISNULL(o.ShipPostalCode,N'')
      AND ISNULL(d.ShipCountry,N'') = ISNULL(o.ShipCountry,N'')
);

COMMIT TRANSACTION;
GO
