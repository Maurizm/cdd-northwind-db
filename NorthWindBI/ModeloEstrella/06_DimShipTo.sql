USE NorthWindDW;
GO
IF OBJECT_ID('dbo.DimShipTo','U') IS NULL
BEGIN
    CREATE TABLE dbo.DimShipTo
    (
        ShipToKey       int IDENTITY(1,1) NOT NULL CONSTRAINT PK_DimShipTo PRIMARY KEY,
        ShipName        nvarchar(40) NULL,
        ShipAddress     nvarchar(60) NULL,
        ShipCity        nvarchar(15) NULL,
        ShipRegion      nvarchar(15) NULL,
        ShipPostalCode  nvarchar(10) NULL,
        ShipCountry     nvarchar(15) NULL
    );
    CREATE INDEX IX_DimShipTo_Location
        ON dbo.DimShipTo(ShipCountry, ShipRegion, ShipCity);
END;
GO
