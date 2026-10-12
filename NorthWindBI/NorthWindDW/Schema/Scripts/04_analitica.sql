USE NorthwindDW;  

-- 1. Ventas netas por año y trimestre
SELECT d.YearNum, d.QuarterNum, COUNT(DISTINCT f.OrderID) AS Pedidos, SUM(f.NetAmount) AS VentasNetas
FROM dbo.FactSales f JOIN dbo.DimDate d ON f.OrderDateKey = d.DateKey
GROUP BY d.YearNum, d.QuarterNum ORDER BY 1, 2;

-- 2. Top 10 clientes
SELECT TOP 10 c.CompanyName, c.Country, SUM(f.NetAmount) AS Ventas
FROM dbo.FactSales f JOIN dbo.DimCustomer c ON f.CustomerKey = c.CustomerKey
GROUP BY c.CompanyName, c.Country ORDER BY SUM(f.NetAmount) DESC;

-- 3. Ventas por categoría y año
SELECT p.CategoryName, d.YearNum, SUM(f.NetAmount) AS Ventas
FROM dbo.FactSales f
JOIN dbo.DimProduct p ON f.ProductKey = p.ProductKey
JOIN dbo.DimDate d ON f.OrderDateKey = d.DateKey
GROUP BY p.CategoryName, d.YearNum ORDER BY 1, 2;

-- 4. Desempeño de vendedores
SELECT e.FullName, e.ManagerName, COUNT(DISTINCT f.OrderID) AS Pedidos, SUM(f.NetAmount) AS Ventas
FROM dbo.FactSales f JOIN dbo.DimEmployee e ON f.EmployeeKey = e.EmployeeKey
GROUP BY e.FullName, e.ManagerName ORDER BY Ventas DESC;

-- 5. Productos más vendidos
SELECT TOP 10 p.ProductName, p.CategoryName, SUM(f.OrderQty) AS Unidades, SUM(f.NetAmount) AS Ventas
FROM dbo.FactSales f JOIN dbo.DimProduct p ON f.ProductKey = p.ProductKey
GROUP BY p.ProductName, p.CategoryName ORDER BY Unidades DESC;

-- 6. Días de entrega promedio por transportista (role-playing de DimDate)
SELECT s.CompanyName, COUNT(DISTINCT f.OrderID) AS Pedidos,
       AVG(DATEDIFF(DAY, do.FullDate, ds.FullDate)) AS DiasPromedioEntrega
FROM dbo.FactSales f
JOIN dbo.DimShipper s ON f.ShipperKey = s.ShipperKey
JOIN dbo.DimDate do ON f.OrderDateKey = do.DateKey
JOIN dbo.DimDate ds ON f.ShippedDateKey = ds.DateKey
WHERE f.ShippedDateKey <> -1
GROUP BY s.CompanyName ORDER BY DiasPromedioEntrega;