CREATE PROCEDURE [dbo].[GetCustomersChangesByRowVersion]
(
   @startRow BIGINT 
   ,@endRow  BIGINT 
)
AS
BEGIN
	SELECT
		c.[CustomerID],
		c.[CompanyName],
		c.[ContactName],
		c.[ContactTitle],
		c.[Address],
		c.[City],
		ISNULL(c.[Region], N'N/A')            AS [Region],
		ISNULL(c.[PostalCode], N'N/A')        AS [PostalCode],
		c.[Country],
		ISNULL(c.[Phone], N'N/A')             AS [Phone],
		ISNULL(c.[Fax], N'N/A')               AS [Fax],
		ISNULL(demo.[Demographics], N'Sin perfil asignado') AS [DemographicsDesc]
	FROM [dbo].[Customers] c
	OUTER APPLY (
		SELECT STRING_AGG(cd.[CustomerDesc], N', ') AS Demographics
		FROM [dbo].[CustomerCustomerDemo] ccd
		INNER JOIN [dbo].[CustomerDemographics] cd
			ON ccd.[CustomerTypeID] = cd.[CustomerTypeID]
		WHERE ccd.[CustomerID] = c.[CustomerID]
	) demo
	WHERE (c.[rowversion] > CONVERT(ROWVERSION,@startRow)
			AND c.[rowversion] <= CONVERT(ROWVERSION,@endRow))
END
GO
