USE NorthWindDW;
GO
-- Modelo: recuento de filas por dimensión y hechos
SELECT 'DimDate' AS Tabla, COUNT_BIG(*) AS Filas FROM dbo.DimDate
UNION ALL SELECT 'DimCustomer', COUNT_BIG(*) FROM dbo.DimCustomer
UNION ALL SELECT 'DimProduct', COUNT_BIG(*) FROM dbo.DimProduct
UNION ALL SELECT 'DimEmployee', COUNT_BIG(*) FROM dbo.DimEmployee
UNION ALL SELECT 'DimShipper', COUNT_BIG(*) FROM dbo.DimShipper
UNION ALL SELECT 'DimShipTo', COUNT_BIG(*) FROM dbo.DimShipTo
UNION ALL SELECT 'FactSales', COUNT_BIG(*) FROM dbo.FactSales;
GO

-- Ventas netas por año
SELECT d.[Year], SUM(f.NetAmount) AS VentasNetas
FROM dbo.FactSales f
JOIN dbo.DimDate d ON d.DateKey = f.OrderDateKey
GROUP BY d.[Year]
ORDER BY d.[Year];
GO

-- Ventas netas por categoría
SELECT p.CategoryName, SUM(f.NetAmount) AS VentasNetas
FROM dbo.FactSales f
JOIN dbo.DimProduct p ON p.ProductKey = f.ProductKey
GROUP BY p.CategoryName
ORDER BY VentasNetas DESC;
GO

-- Comprobar pedidos duplicados por línea
SELECT OrderID, OrderLineNumber, COUNT(*) AS Veces
FROM dbo.FactSales
GROUP BY OrderID, OrderLineNumber
HAVING COUNT(*) > 1;
GO
