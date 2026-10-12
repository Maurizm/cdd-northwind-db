PRINT 'Cargando Dimensiones desde NorthWindOLTP...';
SET NOCOUNT ON;

-- ==============================================================
-- 1. DimCustomer
-- ==============================================================
SET IDENTITY_INSERT [dbo].[DimCustomer] ON;
INSERT INTO [dbo].[DimCustomer] (
    [CustomerKey], [CustomerID], [CompanyName], [ContactName],
    [ContactTitle], [Address], [City], [Region],
    [PostalCode], [Country], [Phone], [Fax], [DemographicsDesc]
)
VALUES (
    -1, N'UNKWN', N'Cliente Desconocido', N'N/A',
    N'N/A', N'N/A', N'N/A', N'N/A',
    N'N/A', N'N/A', N'N/A', N'N/A', N'N/A'
);
SET IDENTITY_INSERT [dbo].[DimCustomer] OFF;

INSERT INTO [dbo].[DimCustomer] (
    [CustomerID], [CompanyName], [ContactName], [ContactTitle],
    [Address], [City], [Region], [PostalCode],
    [Country], [Phone], [Fax], [DemographicsDesc]
)
SELECT
    c.[CustomerID],
    c.[CompanyName],
    c.[ContactName],
    c.[ContactTitle],
    c.[Address],
    c.[City],
    ISNULL(c.[Region], N'N/A'),
    ISNULL(c.[PostalCode], N'N/A'),
    c.[Country],
    ISNULL(c.[Phone], N'N/A'),
    ISNULL(c.[Fax], N'N/A'),
    ISNULL(demo.[Demographics], N'Sin perfil asignado') AS [DemographicsDesc]
FROM [$(OLTP_DB)].[dbo].[Customers] c
OUTER APPLY (
    SELECT STRING_AGG(cd.[CustomerDesc], N', ') AS Demographics
    FROM [$(OLTP_DB)].[dbo].[CustomerCustomerDemo] ccd
    INNER JOIN [$(OLTP_DB)].[dbo].[CustomerDemographics] cd
        ON ccd.[CustomerTypeID] = cd.[CustomerTypeID]
    WHERE ccd.[CustomerID] = c.[CustomerID]
) demo;

PRINT 'DimCustomer cargada: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' registros.';

-- ==============================================================
-- 2. DimEmployee
-- ==============================================================
SET IDENTITY_INSERT [dbo].[DimEmployee] ON;
INSERT INTO [dbo].[DimEmployee] (
    [EmployeeKey], [EmployeeID], [FullName], [LastName],
    [FirstName], [Title], [TitleOfCourtesy], [BirthDate],
    [HireDate], [Address], [City], [Region],
    [PostalCode], [Country], [HomePhone], [Extension],
    [ManagerName], [TerritoriesDesc], [RegionDesc]
)
VALUES (
    -1, -1, N'Empleado Desconocido', N'Desconocido',
    N'N/A', N'N/A', N'N/A', NULL,
    NULL, N'N/A', N'N/A', N'N/A',
    N'N/A', N'N/A', N'N/A', N'N/A',
    N'Sin Supervisor', N'N/A', N'N/A'
);
SET IDENTITY_INSERT [dbo].[DimEmployee] OFF;

INSERT INTO [dbo].[DimEmployee] (
    [EmployeeID], [FullName], [LastName], [FirstName],
    [Title], [TitleOfCourtesy], [BirthDate], [HireDate],
    [Address], [City], [Region], [PostalCode],
    [Country], [HomePhone], [Extension],
    [ManagerName], [TerritoriesDesc], [RegionDesc]
)
SELECT
    e.[EmployeeID],
    CONCAT(e.[FirstName], N' ', e.[LastName]) AS [FullName],
    e.[LastName],
    e.[FirstName],
    e.[Title],
    e.[TitleOfCourtesy],
    CAST(e.[BirthDate] AS DATE),
    CAST(e.[HireDate] AS DATE),
    e.[Address],
    e.[City],
    ISNULL(e.[Region], N'N/A'),
    ISNULL(e.[PostalCode], N'N/A'),
    e.[Country],
    ISNULL(e.[HomePhone], N'N/A'),
    ISNULL(e.[Extension], N'N/A'),
    ISNULL(CONCAT(m.[FirstName], N' ', m.[LastName]), N'Dirección General') AS [ManagerName],
    ISNULL(terr.[Territories], N'Sin territorio') AS [TerritoriesDesc],
    ISNULL(reg.[Regions], N'Sin región') AS [RegionDesc]
FROM [$(OLTP_DB)].[dbo].[Employees] e
LEFT JOIN [$(OLTP_DB)].[dbo].[Employees] m
    ON e.[ReportsTo] = m.[EmployeeID]
OUTER APPLY (
    SELECT STRING_AGG(RTRIM(t.[TerritoryDescription]), N', ') AS Territories
    FROM [$(OLTP_DB)].[dbo].[EmployeeTerritories] et
    INNER JOIN [$(OLTP_DB)].[dbo].[Territories] t
        ON et.[TerritoryID] = t.[TerritoryID]
    WHERE et.[EmployeeID] = e.[EmployeeID]
) terr
OUTER APPLY (
    SELECT STRING_AGG(RegionDescription, N', ') AS Regions
    FROM (
        SELECT DISTINCT RTRIM(r.[RegionDescription]) AS RegionDescription
        FROM [$(OLTP_DB)].[dbo].[EmployeeTerritories] et
        INNER JOIN [$(OLTP_DB)].[dbo].[Territories] t
            ON et.[TerritoryID] = t.[TerritoryID]
        INNER JOIN [$(OLTP_DB)].[dbo].[Region] r
            ON t.[RegionID] = r.[RegionID]
        WHERE et.[EmployeeID] = e.[EmployeeID]
    ) sub
) reg;

PRINT 'DimEmployee cargada: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' registros.';

-- ==============================================================
-- 3. DimProduct
-- ==============================================================
SET IDENTITY_INSERT [dbo].[DimProduct] ON;
INSERT INTO [dbo].[DimProduct] (
    [ProductKey], [ProductID], [ProductName], [CategoryName],
    [CategoryDescription], [SupplierName], [SupplierCountry],
    [QuantityPerUnit], [UnitPrice], [Discontinued], [ProductStatus]
)
VALUES (
    -1, -1, N'Producto Desconocido', N'N/A',
    N'N/A', N'N/A', N'N/A',
    N'N/A', 0, 0, N'Desconocido'
);
SET IDENTITY_INSERT [dbo].[DimProduct] OFF;

INSERT INTO [dbo].[DimProduct] (
    [ProductID], [ProductName], [CategoryName],
    [CategoryDescription], [SupplierName], [SupplierCountry],
    [QuantityPerUnit], [UnitPrice], [Discontinued], [ProductStatus]
)
SELECT
    p.[ProductID],
    p.[ProductName],
    ISNULL(c.[CategoryName], N'Sin Categoría'),
    ISNULL(c.[Description], N'Sin Descripción'),
    ISNULL(s.[CompanyName], N'Sin Proveedor'),
    ISNULL(s.[Country], N'N/A'),
    p.[QuantityPerUnit],
    p.[UnitPrice],
    p.[Discontinued],
    CASE WHEN p.[Discontinued] = 1 THEN N'Descontinuado' ELSE N'Activo' END AS [ProductStatus]
FROM [$(OLTP_DB)].[dbo].[Products] p
LEFT JOIN [$(OLTP_DB)].[dbo].[Categories] c
    ON p.[CategoryID] = c.[CategoryID]
LEFT JOIN [$(OLTP_DB)].[dbo].[Suppliers] s
    ON p.[SupplierID] = s.[SupplierID];

PRINT 'DimProduct cargada: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' registros.';

-- ==============================================================
-- 4. DimShipper
-- ==============================================================
SET IDENTITY_INSERT [dbo].[DimShipper] ON;
INSERT INTO [dbo].[DimShipper] ([ShipperKey], [ShipperID], [CompanyName], [Phone])
VALUES (-1, -1, N'Transportista Desconocido', N'N/A');
SET IDENTITY_INSERT [dbo].[DimShipper] OFF;

INSERT INTO [dbo].[DimShipper] ([ShipperID], [CompanyName], [Phone])
SELECT
    sh.[ShipperID],
    sh.[CompanyName],
    ISNULL(sh.[Phone], N'N/A')
FROM [$(OLTP_DB)].[dbo].[Shippers] sh;

PRINT 'DimShipper cargada: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' registros.';
GO
