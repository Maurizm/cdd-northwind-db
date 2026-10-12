PRINT 'Cargando DimCustomer...';

DELETE FROM [dbo].[DimCustomer];

INSERT INTO [dbo].[DimCustomer]
    ([CustomerID], [CompanyName], [ContactName], [ContactTitle],
     [Address], [City], [Region], [PostalCode], [Country],
     [Phone], [Fax], [CustomerDesc], [IsCurrent])
SELECT 
    c.CustomerID,
    c.CompanyName,
    c.ContactName,
    c.ContactTitle,
    c.Address,
    c.City,
    c.Region,
    c.PostalCode,
    c.Country,
    c.Phone,
    c.Fax,
    cd.CustomerDesc,
    1 AS IsCurrent
FROM [NorthWindOLTP].[dbo].[Customers] c
LEFT JOIN [NorthWindOLTP].[dbo].[CustomerCustomerDemo] ccd 
    ON c.CustomerID = ccd.CustomerID
LEFT JOIN [NorthWindOLTP].[dbo].[CustomerDemographics] cd 
    ON ccd.CustomerTypeID = cd.CustomerTypeID;

PRINT 'DimCustomer cargada: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' registros.';