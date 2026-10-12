/*
=============================================================================
NorthWindDW - Consultas Analíticas de Validación (Business Intelligence)
=============================================================================
*/

-- 1. Validación de cuadre de filas entre OLTP y DW (deben coincidir exactamente)
SELECT 
    (SELECT COUNT(*) FROM [NorthWindOLTP].[dbo].[OrderDetails]) AS Lineas_OLTP,
    (SELECT COUNT(*) FROM [dbo].[FactSales])                     AS Lineas_DW,
    (SELECT SUM(Quantity * UnitPrice * (1 - Discount)) 
     FROM [NorthWindOLTP].[dbo].[OrderDetails])                  AS TotalNeto_OLTP,
    (SELECT SUM(NetAmount) FROM [dbo].[FactSales])               AS TotalNeto_DW;

-- 2. Top 10 Clientes con Mayor Facturación Neta
SELECT TOP 10
    c.[CompanyName],
    c.[Country],
    c.[City],
    COUNT(DISTINCT f.[OrderID]) AS TotalPedidos,
    SUM(f.[Quantity])           AS TotalUnidades,
    SUM(f.[NetAmount])          AS TotalVentasNetas
FROM [dbo].[FactSales] f
INNER JOIN [dbo].[DimCustomer] c ON f.[CustomerKey] = c.[CustomerKey]
GROUP BY c.[CompanyName], c.[Country], c.[City]
ORDER BY TotalVentasNetas DESC;

-- 3. Ventas por Categoría de Producto y Año
SELECT
    p.[CategoryName],
    d.[Year]                    AS Anio,
    SUM(f.[Quantity])           AS UnidadesVendidas,
    SUM(f.[NetAmount])          AS VentasNetas
FROM [dbo].[FactSales] f
INNER JOIN [dbo].[DimProduct] p ON f.[ProductKey] = p.[ProductKey]
INNER JOIN [dbo].[DimDate] d    ON f.[OrderDateKey] = d.[DateKey]
GROUP BY p.[CategoryName], d.[Year]
ORDER BY p.[CategoryName], d.[Year];

-- 4. Desempeño de Vendedores y Supervisión (Jerarquía)
SELECT
    e.[FullName]                AS Vendedor,
    e.[ManagerName]             AS Supervisor,
    e.[RegionDesc]              AS Regiones,
    COUNT(DISTINCT f.[OrderID]) AS TotalOrdenes,
    SUM(f.[NetAmount])          AS VentasNetas
FROM [dbo].[FactSales] f
INNER JOIN [dbo].[DimEmployee] e ON f.[EmployeeKey] = e.[EmployeeKey]
GROUP BY e.[FullName], e.[ManagerName], e.[RegionDesc]
ORDER BY VentasNetas DESC;

-- 5. Top 10 Productos Más Vendidos
SELECT TOP 10
    p.[ProductName],
    p.[CategoryName],
    p.[SupplierName],
    p.[ProductStatus],
    SUM(f.[Quantity])           AS UnidadesTotales,
    SUM(f.[NetAmount])          AS IngresosTotales
FROM [dbo].[FactSales] f
INNER JOIN [dbo].[DimProduct] p ON f.[ProductKey] = p.[ProductKey]
GROUP BY p.[ProductName], p.[CategoryName], p.[SupplierName], p.[ProductStatus]
ORDER BY UnidadesTotales DESC;

-- 6. Tiempo Promedio de Entrega (en días) por Transportista
SELECT
    s.[CompanyName]             AS Transportista,
    COUNT(f.[SalesKey])         AS EnviosRealizados,
    AVG(DATEDIFF(DAY, dOrder.[FullDate], dShip.[FullDate])) AS PromedioDiasEntrega
FROM [dbo].[FactSales] f
INNER JOIN [dbo].[DimShipper] s ON f.[ShipperKey] = s.[ShipperKey]
INNER JOIN [dbo].[DimDate] dOrder ON f.[OrderDateKey] = dOrder.[DateKey]
INNER JOIN [dbo].[DimDate] dShip  ON f.[ShippedDateKey] = dShip.[DateKey]
WHERE f.[ShippedDateKey] <> -1
GROUP BY s.[CompanyName]
ORDER BY PromedioDiasEntrega ASC;
GO
