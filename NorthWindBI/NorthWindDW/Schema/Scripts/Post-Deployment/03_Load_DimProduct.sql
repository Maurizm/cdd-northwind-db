PRINT 'Cargando DimProduct...';

DELETE FROM [dbo].[DimProduct];

INSERT INTO [dbo].[DimProduct]
    ([ProductID], [ProductName], [CategoryName], [CategoryDesc],
     [SupplierName], [SupplierCountry], [QuantityPerUnit],
     [UnitPrice], [Discontinued], [IsCurrent])
SELECT 
    p.ProductID,
    p.ProductName,
    c.CategoryName,
    c.Description,
    s.CompanyName,
    s.Country,
    p.QuantityPerUnit,
    p.UnitPrice,
    p.Discontinued,
    1 AS IsCurrent
FROM [NorthWindOLTP].[dbo].[Products] p
INNER JOIN [NorthWindOLTP].[dbo].[Categories] c 
    ON p.CategoryID = c.CategoryID
INNER JOIN [NorthWindOLTP].[dbo].[Suppliers] s 
    ON p.SupplierID = s.SupplierID;

PRINT 'DimProduct cargada: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' registros.';