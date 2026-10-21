CREATE PROCEDURE [dbo].[GetSuppliersChangesByRowVersion]
(
   @startRow BIGINT 
   ,@endRow  BIGINT 
)
AS
BEGIN
	SELECT
		s.[SupplierID],
		s.[CompanyName],
		s.[ContactName],
		s.[ContactTitle],
		s.[Address],
		s.[City],
		s.[Region],
		s.[PostalCode],
		s.[Country],
		s.[Phone],
		s.[Fax],
		s.[HomePage]
	FROM [dbo].[Suppliers] s
	WHERE (s.[rowversion] > CONVERT(ROWVERSION,@startRow)
			AND s.[rowversion] <= CONVERT(ROWVERSION,@endRow))
END
GO
