PRINT 'Cargando dimensiones desde el OLTP...';
SET NOCOUNT ON;

-- ===== Miembros desconocidos (clave -1) =====
SET IDENTITY_INSERT [dbo].[DimCustomer] ON;
INSERT INTO [dbo].[DimCustomer] ([CustomerKey], [CustomerCode], [CompanyName])
VALUES (-1, N'UNKWN', N'Desconocido');
SET IDENTITY_INSERT [dbo].[DimCustomer] OFF;

SET IDENTITY_INSERT [dbo].[DimEmployee] ON;
INSERT INTO [dbo].[DimEmployee] ([EmployeeKey], [EmployeeCode], [FullName])
VALUES (-1, -1, N'Desconocido');
SET IDENTITY_INSERT [dbo].[DimEmployee] OFF;

SET IDENTITY_INSERT [dbo].[DimProduct] ON;
INSERT INTO [dbo].[DimProduct] ([ProductKey], [ProductCode], [ProductName], [Discontinued], [ProductStatus])
VALUES (-1, -1, N'Desconocido', 0, N'Desconocido');
SET IDENTITY_INSERT [dbo].[DimProduct] OFF;

SET IDENTITY_INSERT [dbo].[DimShipper] ON;
INSERT INTO [dbo].[DimShipper] ([ShipperKey], [ShipperCode], [CompanyName])
VALUES (-1, -1, N'Desconocido');
SET IDENTITY_INSERT [dbo].[DimShipper] OFF;

-- ===== DimCustomer =====
INSERT INTO [dbo].[DimCustomer]
    ([CustomerCode], [CompanyName], [ContactName], [ContactTitle],
     [City], [Region], [PostalCode], [Country], [Phone])
SELECT c.CustomerID, c.CompanyName, c.ContactName, c.ContactTitle,
       c.City, c.Region, c.PostalCode, c.Country, c.Phone
FROM [$(OLTP_DB)].dbo.Customers c;

-- ===== DimEmployee (con jefe, self-join) =====
INSERT INTO [dbo].[DimEmployee]
    ([EmployeeCode], [FullName], [Title], [City], [Country], [HireFullDate], [ManagerName])
SELECT e.EmployeeID, CONCAT(e.FirstName, N' ', e.LastName), e.Title, e.City, e.Country,
       CAST(e.HireDate AS DATE), CONCAT(m.FirstName, N' ', m.LastName)
FROM [$(OLTP_DB)].dbo.Employees e
LEFT JOIN [$(OLTP_DB)].dbo.Employees m ON e.ReportsTo = m.EmployeeID;

-- ===== DimProduct (jerarquía aplanada: producto + categoría + proveedor) =====
INSERT INTO [dbo].[DimProduct]
    ([ProductCode], [ProductName], [CategoryName], [SupplierName], [SupplierCountry],
     [QuantityPerUnit], [ListUnitPrice], [Discontinued], [ProductStatus])
SELECT p.ProductID, p.ProductName, c.CategoryName, s.CompanyName, s.Country,
       p.QuantityPerUnit, p.UnitPrice, p.Discontinued,
       CASE WHEN p.Discontinued = 1 THEN N'Descontinuado' ELSE N'Activo' END
FROM [$(OLTP_DB)].dbo.Products p
LEFT JOIN [$(OLTP_DB)].dbo.Categories c ON p.CategoryID = c.CategoryID
LEFT JOIN [$(OLTP_DB)].dbo.Suppliers s ON p.SupplierID = s.SupplierID;

-- ===== DimShipper =====
INSERT INTO [dbo].[DimShipper] ([ShipperCode], [CompanyName], [Phone])
SELECT sh.ShipperID, sh.CompanyName, sh.Phone
FROM [$(OLTP_DB)].dbo.Shippers sh;