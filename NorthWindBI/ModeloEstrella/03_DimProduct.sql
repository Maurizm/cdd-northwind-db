USE NorthWindDW;
GO
IF OBJECT_ID('dbo.DimProduct','U') IS NULL
BEGIN
    CREATE TABLE dbo.DimProduct
    (
        ProductKey        int IDENTITY(1,1) NOT NULL CONSTRAINT PK_DimProduct PRIMARY KEY,
        ProductID         int NOT NULL,
        ProductName       nvarchar(40) NOT NULL,
        QuantityPerUnit   nvarchar(20) NULL,
        Discontinued      bit NOT NULL,
        UnitPriceCurrent  decimal(19,4) NULL,
        CategoryID        int NULL,
        CategoryName      nvarchar(15) NULL,
        CategoryDescription nvarchar(max) NULL,
        SupplierID        int NULL,
        SupplierName      nvarchar(40) NULL,
        SupplierCity      nvarchar(15) NULL,
        SupplierRegion    nvarchar(15) NULL,
        SupplierCountry   nvarchar(15) NULL,
        ValidFrom         datetime2(0) NOT NULL CONSTRAINT DF_DimProduct_ValidFrom DEFAULT SYSUTCDATETIME(),
        ValidTo           datetime2(0) NOT NULL CONSTRAINT DF_DimProduct_ValidTo DEFAULT ('9999-12-31 23:59:59'),
        IsCurrent         bit NOT NULL CONSTRAINT DF_DimProduct_IsCurrent DEFAULT (1),
        CONSTRAINT CK_DimProduct_Validity CHECK (ValidFrom < ValidTo)
    );
    CREATE INDEX IX_DimProduct_NaturalCurrent
        ON dbo.DimProduct(ProductID, IsCurrent);
END;
GO
