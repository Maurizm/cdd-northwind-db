CREATE TABLE [dbo].[DimProduct](
    [ProductKey]        INT IDENTITY(1,1) NOT NULL,
    [ProductID]         INT NOT NULL,
    [ProductName]       NVARCHAR(40) NOT NULL,
    [CategoryName]      NVARCHAR(15) NOT NULL,
    [CategoryDesc]      NVARCHAR(MAX) NULL,
    [SupplierName]      NVARCHAR(40) NOT NULL,
    [SupplierCountry]   NVARCHAR(15) NULL,
    [QuantityPerUnit]   NVARCHAR(20) NULL,
    [UnitPrice]         MONEY NULL,
    [Discontinued]      BIT NOT NULL,
    [EffectiveDate]     DATETIME NOT NULL DEFAULT GETDATE(),
    [ExpirationDate]    DATETIME NULL,
    [IsCurrent]         BIT NOT NULL DEFAULT 1,
    CONSTRAINT [PK_DimProduct] PRIMARY KEY CLUSTERED ([ProductKey] ASC)
);
GO