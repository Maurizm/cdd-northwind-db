PRINT 'Cargando FactSales...';

DELETE FROM [dbo].[FactSales];

INSERT INTO [dbo].[FactSales]
    ([OrderID], [LineNumber], [ProductKey], [CustomerKey], [EmployeeKey],
     [ShipperKey], [OrderDateKey], [ShipDateKey], [RequiredDateKey],
     [UnitPrice], [Quantity], [Discount], [ExtendedPrice], [Freight], [GrossProfit])
SELECT 
    od.OrderID,
    ROW_NUMBER() OVER (PARTITION BY od.OrderID ORDER BY od.ProductID) AS LineNumber,
    dp.ProductKey,
    dc.CustomerKey,
    de.EmployeeKey,
    ds.ShipperKey,
    CONVERT(INT, CONVERT(VARCHAR(8), o.OrderDate, 112)),
    CASE WHEN o.ShippedDate IS NOT NULL 
         THEN CONVERT(INT, CONVERT(VARCHAR(8), o.ShippedDate, 112)) 
         ELSE NULL END,
    CONVERT(INT, CONVERT(VARCHAR(8), o.RequiredDate, 112)),
    od.UnitPrice,
    od.Quantity,
    od.Discount,
    CONVERT(MONEY, od.UnitPrice * od.Quantity * (1 - od.Discount)),
    CONVERT(MONEY, o.Freight / NULLIF(
        (SELECT COUNT(*) FROM [NorthWindOLTP].[dbo].[OrderDetails] od2 
         WHERE od2.OrderID = od.OrderID), 0)),
    CONVERT(MONEY, od.UnitPrice * od.Quantity * (1 - od.Discount))
FROM [NorthWindOLTP].[dbo].[OrderDetails] od
INNER JOIN [NorthWindOLTP].[dbo].[Orders] o 
    ON od.OrderID = o.OrderID
INNER JOIN [dbo].[DimProduct] dp 
    ON od.ProductID = dp.ProductID AND dp.IsCurrent = 1
INNER JOIN [dbo].[DimCustomer] dc 
    ON o.CustomerID = dc.CustomerID AND dc.IsCurrent = 1
INNER JOIN [dbo].[DimEmployee] de 
    ON o.EmployeeID = de.EmployeeID AND de.IsCurrent = 1
LEFT JOIN [dbo].[DimShipper] ds 
    ON o.ShipVia = ds.ShipperID;

PRINT 'FactSales cargada: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' registros.';