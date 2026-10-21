CREATE PROCEDURE [dbo].[DW_MergeDimProduct]
AS
BEGIN

	UPDATE dp
	SET [ProductName]         = sp.[ProductName]
	   ,[CategoryName]        = sp.[CategoryName]
	   ,[CategoryDescription] = sp.[CategoryDescription]
	   ,[QuantityPerUnit]     = sp.[QuantityPerUnit]
	   ,[ListUnitPrice]       = sp.[ListUnitPrice]
	   ,[Discontinued]        = sp.[Discontinued]
	   ,[ProductStatus]       = sp.[ProductStatus]
	FROM [dbo].[DimProduct]      dp
	INNER JOIN [staging].[product] sp ON (dp.[ProductID] = sp.[ProductID])
END
GO
