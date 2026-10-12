PRINT 'Cargando FactSales desde NorthWindOLTP...';
SET NOCOUNT ON;

;WITH OrderLinesCTE AS (
    SELECT
        od.[OrderID],
        od.[ProductID],
        od.[UnitPrice],
        od.[Quantity],
        od.[Discount],
        o.[CustomerID],
        o.[EmployeeID],
        o.[ShipVia],
        o.[OrderDate],
        o.[ShippedDate],
        o.[RequiredDate],
        o.[Freight],
        ROW_NUMBER() OVER (PARTITION BY od.[OrderID] ORDER BY od.[ProductID]) AS OrderLineNum,
        COUNT(*) OVER (PARTITION BY od.[OrderID]) AS TotalLinesInOrder
    FROM [$(OLTP_DB)].[dbo].[OrderDetails] od
    INNER JOIN [$(OLTP_DB)].[dbo].[Orders] o
        ON od.[OrderID] = o.[OrderID]
)
INSERT INTO [dbo].[FactSales] (
    [OrderDateKey],
    [ShippedDateKey],
    [RequiredDateKey],
    [CustomerKey],
    [EmployeeKey],
    [ProductKey],
    [ShipperKey],
    [OrderID],
    [OrderLineNum],
    [Quantity],
    [UnitPrice],
    [Discount],
    [GrossAmount],
    [DiscountAmount],
    [NetAmount],
    [Freight],
    [AllocatedFreight]
)
SELECT
    ISNULL(ddOrder.[DateKey], -1) AS [OrderDateKey],
    ISNULL(ddShipped.[DateKey], -1) AS [ShippedDateKey],
    ISNULL(ddRequired.[DateKey], -1) AS [RequiredDateKey],
    ISNULL(dc.[CustomerKey], -1) AS [CustomerKey],
    ISNULL(de.[EmployeeKey], -1) AS [EmployeeKey],
    ISNULL(dp.[ProductKey], -1) AS [ProductKey],
    ISNULL(ds.[ShipperKey], -1) AS [ShipperKey],
    cte.[OrderID],
    cte.[OrderLineNum],
    cte.[Quantity],
    cte.[UnitPrice],
    cte.[Discount],
    CONVERT(MONEY, cte.[Quantity] * cte.[UnitPrice]) AS [GrossAmount],
    CONVERT(MONEY, cte.[Quantity] * cte.[UnitPrice] * cte.[Discount]) AS [DiscountAmount],
    CONVERT(MONEY, cte.[Quantity] * cte.[UnitPrice] * (1 - cte.[Discount])) AS [NetAmount],
    cte.[Freight],
    CONVERT(MONEY, cte.[Freight] / NULLIF(cte.[TotalLinesInOrder], 0)) AS [AllocatedFreight]
FROM OrderLinesCTE cte
LEFT JOIN [dbo].[DimDate] ddOrder
    ON ddOrder.[FullDate] = CAST(cte.[OrderDate] AS DATE)
LEFT JOIN [dbo].[DimDate] ddShipped
    ON ddShipped.[FullDate] = CAST(cte.[ShippedDate] AS DATE)
LEFT JOIN [dbo].[DimDate] ddRequired
    ON ddRequired.[FullDate] = CAST(cte.[RequiredDate] AS DATE)
LEFT JOIN [dbo].[DimCustomer] dc
    ON dc.[CustomerID] = cte.[CustomerID]
LEFT JOIN [dbo].[DimEmployee] de
    ON de.[EmployeeID] = cte.[EmployeeID]
LEFT JOIN [dbo].[DimProduct] dp
    ON dp.[ProductID] = cte.[ProductID]
LEFT JOIN [dbo].[DimShipper] ds
    ON ds.[ShipperID] = cte.[ShipVia];

PRINT 'FactSales cargada exitosamente: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' registros.';
GO
