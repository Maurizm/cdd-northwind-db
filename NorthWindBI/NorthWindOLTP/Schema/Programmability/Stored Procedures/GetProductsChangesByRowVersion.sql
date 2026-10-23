CREATE PROCEDURE [dbo].[GetProductsChangesByRowVersion]
(
   @startRow BIGINT 
   ,@endRow  BIGINT 
)
AS
BEGIN
	SELECT
		p.[ProductID],
		p.[ProductName],
		p.[SupplierID],
		ISNULL(c.[CategoryName], N'Sin Categoría')   AS [CategoryName],
		ISNULL(c.[Description], N'Sin Descripción')  AS [CategoryDescription],
		p.[QuantityPerUnit],
		p.[UnitPrice]                                AS [ListUnitPrice],
		p.[Discontinued],
		CAST(CASE WHEN p.[Discontinued] = 1 THEN N'Descontinuado' ELSE N'Activo' END AS NVARCHAR(15)) AS [ProductStatus]
	FROM [dbo].[Products] p
	LEFT JOIN [dbo].[Categories] c
		ON p.[CategoryID] = c.[CategoryID]
	WHERE (p.[rowversion] > CONVERT(ROWVERSION,@startRow)
			AND p.[rowversion] <= CONVERT(ROWVERSION,@endRow))
	OR (c.[rowversion] > CONVERT(ROWVERSION,@startRow)
			AND c.[rowversion] <= CONVERT(ROWVERSION,@endRow))
END
GO
