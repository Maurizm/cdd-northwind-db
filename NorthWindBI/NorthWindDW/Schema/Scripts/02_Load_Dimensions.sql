PRINT 'Cargando Dimensiones desde NorthWindOLTP...';
SET NOCOUNT ON;

-- ==============================================================
-- 1. DimGeography (dimensión conformada: Customers + Employees + Suppliers)
-- ==============================================================
SET IDENTITY_INSERT [dbo].[DimGeography] ON;
INSERT INTO [dbo].[DimGeography] ([GeographyKey], [City], [Region], [Country])
VALUES (-1, N'Desconocido', N'Desconocido', N'Desconocido');
SET IDENTITY_INSERT [dbo].[DimGeography] OFF;

INSERT INTO [dbo].[DimGeography] ([City], [Region], [Country])
SELECT DISTINCT norm.[City], norm.[Region], norm.[Country]
FROM (
    SELECT LTRIM(RTRIM(COALESCE(c.[City], N'')))    AS [City],
           LTRIM(RTRIM(COALESCE(c.[Region], N'')))  AS [Region],
           LTRIM(RTRIM(COALESCE(c.[Country], N''))) AS [Country]
    FROM [$(OLTP_DB)].[dbo].[Customers] c
    UNION ALL
    SELECT LTRIM(RTRIM(COALESCE(e.[City], N''))),
           LTRIM(RTRIM(COALESCE(e.[Region], N''))),
           LTRIM(RTRIM(COALESCE(e.[Country], N'')))
    FROM [$(OLTP_DB)].[dbo].[Employees] e
    UNION ALL
    SELECT LTRIM(RTRIM(COALESCE(s.[City], N''))),
           LTRIM(RTRIM(COALESCE(s.[Region], N''))),
           LTRIM(RTRIM(COALESCE(s.[Country], N'')))
    FROM [$(OLTP_DB)].[dbo].[Suppliers] s
) norm
WHERE NOT (norm.[City] = N'' AND norm.[Region] = N'' AND norm.[Country] = N'');

PRINT 'DimGeography cargada: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' registros.';

-- ==============================================================
-- 2. DimCustomer
-- ==============================================================
SET IDENTITY_INSERT [dbo].[DimCustomer] ON;
INSERT INTO [dbo].[DimCustomer] (
    [CustomerKey], [CustomerID], [CompanyName], [ContactName],
    [ContactTitle], [Address], [PostalCode], [Phone],
    [Fax], [DemographicsDesc], [GeographyKey]
)
VALUES (
    -1, N'UNKWN', N'Cliente Desconocido', N'N/A',
    N'N/A', N'N/A', N'N/A', N'N/A',
    N'N/A', N'N/A', -1
);
SET IDENTITY_INSERT [dbo].[DimCustomer] OFF;

INSERT INTO [dbo].[DimCustomer] (
    [CustomerID], [CompanyName], [ContactName], [ContactTitle],
    [Address], [PostalCode], [Phone], [Fax],
    [DemographicsDesc], [GeographyKey]
)
SELECT
    c.[CustomerID],
    c.[CompanyName],
    c.[ContactName],
    c.[ContactTitle],
    c.[Address],
    ISNULL(c.[PostalCode], N'N/A'),
    ISNULL(c.[Phone], N'N/A'),
    ISNULL(c.[Fax], N'N/A'),
    ISNULL(demo.[Demographics], N'Sin perfil asignado') AS [DemographicsDesc],
    ISNULL(g.[GeographyKey], -1)
FROM [$(OLTP_DB)].[dbo].[Customers] c
OUTER APPLY (
    SELECT STRING_AGG(cd.[CustomerDesc], N', ') AS Demographics
    FROM [$(OLTP_DB)].[dbo].[CustomerCustomerDemo] ccd
    INNER JOIN [$(OLTP_DB)].[dbo].[CustomerDemographics] cd
        ON ccd.[CustomerTypeID] = cd.[CustomerTypeID]
    WHERE ccd.[CustomerID] = c.[CustomerID]
) demo
LEFT JOIN [dbo].[DimGeography] g
    ON g.[City]    = LTRIM(RTRIM(COALESCE(c.[City],    N'')))
   AND g.[Region]  = LTRIM(RTRIM(COALESCE(c.[Region],  N'')))
   AND g.[Country] = LTRIM(RTRIM(COALESCE(c.[Country], N'')));

PRINT 'DimCustomer cargada: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' registros.';

-- ==============================================================
-- 3. DimEmployee
-- ==============================================================
SET IDENTITY_INSERT [dbo].[DimEmployee] ON;
INSERT INTO [dbo].[DimEmployee] (
    [EmployeeKey], [EmployeeID], [FullName], [LastName],
    [FirstName], [Title], [TitleOfCourtesy], [BirthDate],
    [HireDate], [Address], [PostalCode], [HomePhone],
    [Extension], [ManagerName], [TerritoriesDesc], [RegionDesc],
    [GeographyKey]
)
VALUES (
    -1, -1, N'Empleado Desconocido', N'Desconocido',
    N'N/A', N'N/A', N'N/A', NULL,
    NULL, N'N/A', N'N/A', N'N/A',
    N'N/A', N'Sin Supervisor', N'N/A', N'N/A',
    -1
);
SET IDENTITY_INSERT [dbo].[DimEmployee] OFF;

INSERT INTO [dbo].[DimEmployee] (
    [EmployeeID], [FullName], [LastName], [FirstName],
    [Title], [TitleOfCourtesy], [BirthDate], [HireDate],
    [Address], [PostalCode], [HomePhone], [Extension],
    [ManagerName], [TerritoriesDesc], [RegionDesc], [GeographyKey]
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
    ISNULL(e.[PostalCode], N'N/A'),
    ISNULL(e.[HomePhone], N'N/A'),
    ISNULL(e.[Extension], N'N/A'),
    ISNULL(CONCAT(m.[FirstName], N' ', m.[LastName]), N'Dirección General') AS [ManagerName],
    ISNULL(terr.[Territories], N'Sin territorio') AS [TerritoriesDesc],
    ISNULL(reg.[Regions], N'Sin región') AS [RegionDesc],
    ISNULL(g.[GeographyKey], -1)
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
) reg
LEFT JOIN [dbo].[DimGeography] g
    ON g.[City]    = LTRIM(RTRIM(COALESCE(e.[City],    N'')))
   AND g.[Region]  = LTRIM(RTRIM(COALESCE(e.[Region],  N'')))
   AND g.[Country] = LTRIM(RTRIM(COALESCE(e.[Country], N'')));

PRINT 'DimEmployee cargada: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' registros.';

-- ==============================================================
-- 4. DimProduct
-- ==============================================================
SET IDENTITY_INSERT [dbo].[DimProduct] ON;
INSERT INTO [dbo].[DimProduct] (
    [ProductKey], [ProductID], [ProductName], [CategoryName],
    [CategoryDescription], [QuantityPerUnit], [ListUnitPrice],
    [Discontinued], [ProductStatus]
)
VALUES (
    -1, -1, N'Producto Desconocido', N'N/A',
    N'N/A', N'N/A', 0, 0, N'Desconocido'
);
SET IDENTITY_INSERT [dbo].[DimProduct] OFF;

INSERT INTO [dbo].[DimProduct] (
    [ProductID], [ProductName], [CategoryName],
    [CategoryDescription], [QuantityPerUnit], [ListUnitPrice],
    [Discontinued], [ProductStatus]
)
SELECT
    p.[ProductID],
    p.[ProductName],
    ISNULL(c.[CategoryName], N'Sin Categoría'),
    ISNULL(c.[Description], N'Sin Descripción'),
    p.[QuantityPerUnit],
    p.[UnitPrice],
    p.[Discontinued],
    CASE WHEN p.[Discontinued] = 1 THEN N'Descontinuado' ELSE N'Activo' END AS [ProductStatus]
FROM [$(OLTP_DB)].[dbo].[Products] p
LEFT JOIN [$(OLTP_DB)].[dbo].[Categories] c
    ON p.[CategoryID] = c.[CategoryID];

PRINT 'DimProduct cargada: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' registros.';

-- ==============================================================
-- 5. DimSupplier
-- ==============================================================
SET IDENTITY_INSERT [dbo].[DimSupplier] ON;
INSERT INTO [dbo].[DimSupplier] (
    [SupplierKey], [SupplierID], [CompanyName], [ContactName],
    [ContactTitle], [Address], [PostalCode], [Phone],
    [Fax], [HomePage], [GeographyKey]
)
VALUES (
    -1, -1, N'Proveedor Desconocido', N'N/A',
    N'N/A', N'N/A', N'N/A', N'N/A',
    N'N/A', N'N/A', -1
);
SET IDENTITY_INSERT [dbo].[DimSupplier] OFF;

INSERT INTO [dbo].[DimSupplier] (
    [SupplierID], [CompanyName], [ContactName], [ContactTitle],
    [Address], [PostalCode], [Phone], [Fax],
    [HomePage], [GeographyKey]
)
SELECT
    s.[SupplierID],
    s.[CompanyName],
    s.[ContactName],
    s.[ContactTitle],
    s.[Address],
    s.[PostalCode],
    s.[Phone],
    s.[Fax],
    s.[HomePage],
    ISNULL(g.[GeographyKey], -1)
FROM [$(OLTP_DB)].[dbo].[Suppliers] s
LEFT JOIN [dbo].[DimGeography] g
    ON g.[City]    = LTRIM(RTRIM(COALESCE(s.[City],    N'')))
   AND g.[Region]  = LTRIM(RTRIM(COALESCE(s.[Region],  N'')))
   AND g.[Country] = LTRIM(RTRIM(COALESCE(s.[Country], N'')));

PRINT 'DimSupplier cargada: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' registros.';

-- ==============================================================
-- 6. DimShipper
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
