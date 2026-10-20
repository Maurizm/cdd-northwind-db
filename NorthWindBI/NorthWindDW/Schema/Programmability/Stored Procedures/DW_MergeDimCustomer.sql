CREATE PROCEDURE [dbo].[DW_MergeDimCustomer]
AS
BEGIN

	-- 1. Upsert de lugares nuevos en DimGeography (dimensión conformada)
	INSERT INTO [dbo].[DimGeography] ([City], [Region], [Country])
	SELECT DISTINCT norm.[City], norm.[Region], norm.[Country]
	FROM (
		SELECT
			LTRIM(RTRIM(COALESCE(sc.[City],    N''))) AS [City],
			LTRIM(RTRIM(COALESCE(sc.[Region],  N''))) AS [Region],
			LTRIM(RTRIM(COALESCE(sc.[Country], N''))) AS [Country]
		FROM [staging].[customer] sc
	) norm
	WHERE NOT (norm.[City] = N'' AND norm.[Region] = N'' AND norm.[Country] = N'')
		AND NOT EXISTS (
			SELECT 1
			FROM [dbo].[DimGeography] g
			WHERE g.[City] = norm.[City]
				AND g.[Region] = norm.[Region]
				AND g.[Country] = norm.[Country]
		);

	-- 2. Update de filas existentes, resolviendo GeographyKey
	UPDATE dc
	SET [CompanyName]      = sc.[CompanyName]
	   ,[ContactName]      = sc.[ContactName]
	   ,[ContactTitle]     = sc.[ContactTitle]
	   ,[Address]          = sc.[Address]
	   ,[PostalCode]       = sc.[PostalCode]
	   ,[Phone]            = sc.[Phone]
	   ,[Fax]              = sc.[Fax]
	   ,[DemographicsDesc] = sc.[DemographicsDesc]
	   ,[GeographyKey]     = ISNULL(g.[GeographyKey], -1)
	FROM [dbo].[DimCustomer]      dc
	INNER JOIN [staging].[customer] sc ON (dc.[CustomerID] = sc.[CustomerID])
	LEFT JOIN [dbo].[DimGeography] g
		ON g.[City]    = LTRIM(RTRIM(COALESCE(sc.[City],    N'')))
	   AND g.[Region]  = LTRIM(RTRIM(COALESCE(sc.[Region],  N'')))
	   AND g.[Country] = LTRIM(RTRIM(COALESCE(sc.[Country], N'')))
END
GO
