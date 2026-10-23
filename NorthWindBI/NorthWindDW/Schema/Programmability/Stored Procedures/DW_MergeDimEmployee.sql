CREATE PROCEDURE [dbo].[DW_MergeDimEmployee]
AS
BEGIN

	-- 1. Upsert de lugares nuevos en DimGeography (dimensión conformada)
	INSERT INTO [dbo].[DimGeography] ([City], [Region], [Country])
	SELECT DISTINCT norm.[City], norm.[Region], norm.[Country]
	FROM (
		SELECT
			LTRIM(RTRIM(COALESCE(se.[City],    N''))) AS [City],
			LTRIM(RTRIM(COALESCE(se.[Region],  N''))) AS [Region],
			LTRIM(RTRIM(COALESCE(se.[Country], N''))) AS [Country]
		FROM [staging].[employee] se
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
	UPDATE de
	SET [FullName]        = se.[FullName]
	   ,[LastName]        = se.[LastName]
	   ,[FirstName]       = se.[FirstName]
	   ,[Title]           = se.[Title]
	   ,[TitleOfCourtesy] = se.[TitleOfCourtesy]
	   ,[BirthDate]       = se.[BirthDate]
	   ,[HireDate]        = se.[HireDate]
	   ,[Address]         = se.[Address]
	   ,[PostalCode]      = se.[PostalCode]
	   ,[HomePhone]       = se.[HomePhone]
	   ,[Extension]       = se.[Extension]
	   ,[ManagerName]     = se.[ManagerName]
	   ,[TerritoriesDesc] = se.[TerritoriesDesc]
	   ,[RegionDesc]      = se.[RegionDesc]
	   ,[GeographyKey]    = ISNULL(g.[GeographyKey], -1)
	FROM [dbo].[DimEmployee]      de
	INNER JOIN [staging].[employee] se ON (de.[EmployeeID] = se.[EmployeeID])
	LEFT JOIN [dbo].[DimGeography] g
		ON g.[City]    = LTRIM(RTRIM(COALESCE(se.[City],    N'')))
	   AND g.[Region]  = LTRIM(RTRIM(COALESCE(se.[Region],  N'')))
	   AND g.[Country] = LTRIM(RTRIM(COALESCE(se.[Country], N'')))
END
GO
