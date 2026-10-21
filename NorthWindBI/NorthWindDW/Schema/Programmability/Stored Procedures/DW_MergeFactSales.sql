CREATE PROCEDURE [dbo].[DW_MergeFactSales]
AS
BEGIN

	UPDATE f
	SET [OrderDateKey]     = ss.[OrderDateKey]
	   ,[RequiredDateKey]  = ss.[RequiredDateKey]
	   ,[ShippedDateKey]   = ss.[ShippedDateKey]
	   ,[CustomerKey]      = ss.[CustomerKey]
	   ,[EmployeeKey]      = ss.[EmployeeKey]
	   ,[ProductKey]       = ss.[ProductKey]
	   ,[SupplierKey]      = ss.[SupplierKey]
	   ,[ShipperKey]       = ss.[ShipperKey]
	   ,[Quantity]         = ss.[Quantity]
	   ,[UnitPrice]        = ss.[UnitPrice]
	   ,[Discount]         = ss.[Discount]
	   ,[GrossAmount]      = ss.[GrossAmount]
	   ,[DiscountAmount]   = ss.[DiscountAmount]
	   ,[NetAmount]        = ss.[NetAmount]
	   ,[Freight]          = ss.[Freight]
	   ,[AllocatedFreight] = ss.[AllocatedFreight]
	FROM [dbo].[FactSales]     f
	INNER JOIN [staging].[sales] ss
		ON (f.[OrderID] = ss.[OrderID] AND f.[OrderLineNum] = ss.[OrderLineNum])
END
GO
