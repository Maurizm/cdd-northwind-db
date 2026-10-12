USE NorthWindDW;
GO
IF OBJECT_ID('dbo.DimShipper','U') IS NULL
BEGIN
    CREATE TABLE dbo.DimShipper
    (
        ShipperKey    int IDENTITY(1,1) NOT NULL CONSTRAINT PK_DimShipper PRIMARY KEY,
        ShipperID     int NOT NULL,
        CompanyName   nvarchar(40) NOT NULL,
        Phone         nvarchar(24) NULL,
        IsCurrent     bit NOT NULL CONSTRAINT DF_DimShipper_IsCurrent DEFAULT (1)
    );
    CREATE INDEX IX_DimShipper_NaturalCurrent
        ON dbo.DimShipper(ShipperID, IsCurrent);
END;
GO
