PRINT 'Cargando DimEmployee...';

DELETE FROM [dbo].[DimEmployee];

INSERT INTO [dbo].[DimEmployee]
    ([EmployeeID], [FullName], [LastName], [FirstName], [Title],
     [TitleOfCourtesy], [BirthDate], [HireDate], [Address], [City],
     [Region], [PostalCode], [Country], [HomePhone], [Extension],
     [TerritoryDesc], [RegionDesc], [IsCurrent])
SELECT 
    e.EmployeeID,
    e.FirstName + ' ' + e.LastName AS FullName,
    e.LastName,
    e.FirstName,
    e.Title,
    e.TitleOfCourtesy,
    e.BirthDate,
    e.HireDate,
    e.Address,
    e.City,
    e.Region,
    e.PostalCode,
    e.Country,
    e.HomePhone,
    e.Extension,
    ISNULL(t.Territories, 'N/A') AS TerritoryDesc,
    ISNULL(r.Regions, 'N/A') AS RegionDesc,
    1 AS IsCurrent
FROM [NorthWindOLTP].[dbo].[Employees] e
OUTER APPLY (
    SELECT STRING_AGG(t2.TerritoryDescription, ', ') AS Territories
    FROM [NorthWindOLTP].[dbo].[EmployeeTerritories] et
    INNER JOIN [NorthWindOLTP].[dbo].[Territories] t2 
        ON et.TerritoryID = t2.TerritoryID
    WHERE et.EmployeeID = e.EmployeeID
) t
OUTER APPLY (
    SELECT STRING_AGG(r2.RegionDescription, ', ') AS Regions
    FROM [NorthWindOLTP].[dbo].[EmployeeTerritories] et
    INNER JOIN [NorthWindOLTP].[dbo].[Territories] t2 
        ON et.TerritoryID = t2.TerritoryID
    INNER JOIN [NorthWindOLTP].[dbo].[Region] r2 
        ON t2.RegionID = r2.RegionID
    WHERE et.EmployeeID = e.EmployeeID
) r;

PRINT 'DimEmployee cargada: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' registros.';