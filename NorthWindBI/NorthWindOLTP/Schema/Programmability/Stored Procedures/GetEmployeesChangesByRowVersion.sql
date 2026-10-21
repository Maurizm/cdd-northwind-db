CREATE PROCEDURE [dbo].[GetEmployeesChangesByRowVersion]
(
   @startRow BIGINT 
   ,@endRow  BIGINT 
)
AS
BEGIN
	SELECT
		e.[EmployeeID],
		CONCAT(e.[FirstName], N' ', e.[LastName]) AS [FullName],
		e.[LastName],
		e.[FirstName],
		e.[Title],
		e.[TitleOfCourtesy],
		CAST(e.[BirthDate] AS DATE)              AS [BirthDate],
		CAST(e.[HireDate] AS DATE)               AS [HireDate],
		e.[Address],
		e.[City],
		ISNULL(e.[Region], N'N/A')               AS [Region],
		ISNULL(e.[PostalCode], N'N/A')           AS [PostalCode],
		e.[Country],
		ISNULL(e.[HomePhone], N'N/A')            AS [HomePhone],
		ISNULL(e.[Extension], N'N/A')            AS [Extension],
		ISNULL(CONCAT(m.[FirstName], N' ', m.[LastName]), N'Dirección General') AS [ManagerName],
		ISNULL(terr.[Territories], N'Sin territorio') AS [TerritoriesDesc],
		ISNULL(reg.[Regions], N'Sin región')     AS [RegionDesc]
	FROM [dbo].[Employees] e
	LEFT JOIN [dbo].[Employees] m
		ON e.[ReportsTo] = m.[EmployeeID]
	OUTER APPLY (
		SELECT STRING_AGG(RTRIM(t.[TerritoryDescription]), N', ') AS Territories
		FROM [dbo].[EmployeeTerritories] et
		INNER JOIN [dbo].[Territories] t
			ON et.[TerritoryID] = t.[TerritoryID]
		WHERE et.[EmployeeID] = e.[EmployeeID]
	) terr
	OUTER APPLY (
		SELECT STRING_AGG(RegionDescription, N', ') AS Regions
		FROM (
			SELECT DISTINCT RTRIM(r.[RegionDescription]) AS RegionDescription
			FROM [dbo].[EmployeeTerritories] et
			INNER JOIN [dbo].[Territories] t
				ON et.[TerritoryID] = t.[TerritoryID]
			INNER JOIN [dbo].[Region] r
				ON t.[RegionID] = r.[RegionID]
			WHERE et.[EmployeeID] = e.[EmployeeID]
		) sub
	) reg
	WHERE (e.[rowversion] > CONVERT(ROWVERSION,@startRow)
			AND e.[rowversion] <= CONVERT(ROWVERSION,@endRow))
	OR EXISTS (
		SELECT 1
		FROM [dbo].[EmployeeTerritories] et2
		WHERE et2.[EmployeeID] = e.[EmployeeID]
			AND et2.[rowversion] > CONVERT(ROWVERSION,@startRow)
			AND et2.[rowversion] <= CONVERT(ROWVERSION,@endRow)
	)
END
GO
