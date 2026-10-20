CREATE PROCEDURE [dbo].[GetShippersChangesByRowVersion]
(
   @startRow BIGINT 
   ,@endRow  BIGINT 
)
AS
BEGIN
	SELECT
		sh.[ShipperID],
		sh.[CompanyName],
		ISNULL(sh.[Phone], N'N/A') AS [Phone]
	FROM [dbo].[Shippers] sh
	WHERE (sh.[rowversion] > CONVERT(ROWVERSION,@startRow)
			AND sh.[rowversion] <= CONVERT(ROWVERSION,@endRow))
END
GO
