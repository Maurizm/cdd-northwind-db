CREATE PROCEDURE [dbo].[DW_MergeDimSupplier]
AS
BEGIN

	-- 1. Upsert de lugares nuevos en DimGeography (dimensión conformada)
	INSERT INTO [dbo].[DimGeography] ([City], [Region], [Country])
	SELECT DISTINCT norm.[City], norm.[Region], norm.[Country]
	FROM (
		SELECT
			LTRIM(RTRIM(COALESCE(ss.[City],    N''))) AS [City],
			LTRIM(RTRIM(COALESCE(ss.[Region],  N''))) AS [Region],
			LTRIM(RTRIM(COALESCE(ss.[Country], N''))) AS [Country]
		FROM [staging].[supplier] ss
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
	UPDATE ds
	SET [CompanyName]   = ss.[CompanyName]
	   ,[ContactName]   = ss.[ContactName]
	   ,[ContactTitle]  = ss.[ContactTitle]
	   ,[Address]       = ss.[Address]
	   ,[PostalCode]    = ss.[PostalCode]
	   ,[Phone]         = ss.[Phone]
	   ,[Fax]           = ss.[Fax]
	   ,[HomePage]      = ss.[HomePage]
	   ,[GeographyKey]  = ISNULL(g.[GeographyKey], -1)
	FROM [dbo].[DimSupplier]      ds
	INNER JOIN [staging].[supplier] ss ON (ds.[SupplierID] = ss.[SupplierID])
	LEFT JOIN [dbo].[DimGeography] g
		ON g.[City]    = LTRIM(RTRIM(COALESCE(ss.[City],    N'')))
	   AND g.[Region]  = LTRIM(RTRIM(COALESCE(ss.[Region],  N'')))
	   AND g.[Country] = LTRIM(RTRIM(COALESCE(ss.[Country], N'')))
END
GO
