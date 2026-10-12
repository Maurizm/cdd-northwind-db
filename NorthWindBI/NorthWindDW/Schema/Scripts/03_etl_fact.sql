PRINT 'Cargando FactSales (1 fila por línea de pedido)...';
SET NOCOUNT ON;

;WITH Lineas AS
(
    SELECT
        od.OrderID, od.ProductID, od.UnitPrice, od.Quantity, od.Discount,
        o.CustomerID, o.EmployeeID, o.ShipVia, o.OrderDate, o.ShippedDate,
        ROW_NUMBER() OVER (PARTITION BY od.OrderID ORDER BY od.ProductID) AS LineNum
    FROM [$(OLTP_DB)].dbo.OrderDetails od
    INNER JOIN [$(OLTP_DB)].dbo.Orders o ON o.OrderID = od.OrderID
)
INSERT INTO [dbo].[FactSales]
    ([OrderDateKey], [ShippedDateKey], [CustomerKey], [EmployeeKey], [ProductKey], [ShipperKey],
     [OrderID], [OrderLineNum], [OrderQty], [UnitPrice], [DiscountRate],
     [GrossAmount], [DiscountAmount], [NetAmount])
SELECT
    ISNULL(dd.DateKey, -1),
    ISNULL(sd.DateKey, -1),
    ISNULL(dc.CustomerKey, -1),
    ISNULL(de.EmployeeKey, -1),
    ISNULL(dp.ProductKey, -1),
    ISNULL(ds.ShipperKey, -1),
    L.OrderID, L.LineNum, L.Quantity, L.UnitPrice, L.Discount,
    CONVERT(MONEY, L.UnitPrice * L.Quantity),
    CONVERT(MONEY, L.UnitPrice * L.Quantity * L.Discount),
    CONVERT(MONEY, L.UnitPrice * L.Quantity * (1 - L.Discount))
FROM Lineas L
LEFT JOIN [dbo].[DimDate]     dd ON dd.FullDate = CAST(L.OrderDate AS DATE)
LEFT JOIN [dbo].[DimDate]     sd ON sd.FullDate = CAST(L.ShippedDate AS DATE)
LEFT JOIN [dbo].[DimCustomer] dc ON dc.CustomerCode = L.CustomerID
LEFT JOIN [dbo].[DimEmployee] de ON de.EmployeeCode = L.EmployeeID
LEFT JOIN [dbo].[DimProduct]  dp ON dp.ProductCode  = L.ProductID
LEFT JOIN [dbo].[DimShipper]  ds ON ds.ShipperCode  = L.ShipVia;