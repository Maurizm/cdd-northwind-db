PRINT 'Cargando DimShipper...';

DELETE FROM [dbo].[DimShipper];

INSERT INTO [dbo].[DimShipper]
    ([ShipperID], [CompanyName], [Phone])
SELECT 
    ShipperID, 
    CompanyName, 
    Phone
FROM [NorthWindOLTP].[dbo].[Shippers];

PRINT 'DimShipper cargada: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' registros.';