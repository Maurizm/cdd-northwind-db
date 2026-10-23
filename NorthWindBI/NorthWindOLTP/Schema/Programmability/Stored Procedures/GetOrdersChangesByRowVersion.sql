CREATE PROCEDURE [dbo].[GetOrdersChangesByRowVersion]
(
   @startRow BIGINT 
   ,@endRow  BIGINT 
)
AS
BEGIN
	;WITH ChangedOrders AS (
		SELECT o.[OrderID]
		FROM [dbo].[Orders] o
		WHERE o.[rowversion] > CONVERT(ROWVERSION,@startRow)
			AND o.[rowversion] <= CONVERT(ROWVERSION,@endRow)
		UNION
		SELECT od.[OrderID]
		FROM [dbo].[OrderDetails] od
		WHERE od.[rowversion] > CONVERT(ROWVERSION,@startRow)
			AND od.[rowversion] <= CONVERT(ROWVERSION,@endRow)
	)
	SELECT
		od.[OrderID],
		CONVERT(SMALLINT, ROW_NUMBER() OVER (PARTITION BY od.[OrderID] ORDER BY od.[ProductID])) AS [OrderLineNum],
		CASE WHEN o.[OrderDate] IS NULL THEN -1
			 ELSE CONVERT(INT, CONVERT(VARCHAR(8), o.[OrderDate], 112))
		END                                                     AS [OrderDateKey],
		CASE WHEN o.[RequiredDate] IS NULL THEN -1
			 ELSE CONVERT(INT, CONVERT(VARCHAR(8), o.[RequiredDate], 112))
		END                                                     AS [RequiredDateKey],
		CASE WHEN o.[ShippedDate] IS NULL THEN -1
			 ELSE CONVERT(INT, CONVERT(VARCHAR(8), o.[ShippedDate], 112))
		END                                                     AS [ShippedDateKey],
		o.[CustomerID],
		o.[EmployeeID],
		od.[ProductID],
		o.[ShipVia]                                             AS [ShipperID],
		p.[SupplierID],
		od.[Quantity],
		od.[UnitPrice],
		od.[Discount],
		o.[Freight],
		COUNT(*) OVER (PARTITION BY od.[OrderID])               AS [TotalLinesInOrder],
		o.[OrderDate],
		o.[RequiredDate],
		o.[ShippedDate]
	FROM [dbo].[OrderDetails] od
	INNER JOIN ChangedOrders co
		ON od.[OrderID] = co.[OrderID]
	INNER JOIN [dbo].[Orders] o
		ON od.[OrderID] = o.[OrderID]
	INNER JOIN [dbo].[Products] p
		ON od.[ProductID] = p.[ProductID]
END
GO
