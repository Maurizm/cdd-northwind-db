CREATE TABLE [dbo].[DimProduct] (
    [ProductKey]            INT IDENTITY(1,1) NOT NULL,
    [ProductID]             INT NOT NULL,
    [ProductName]           NVARCHAR(40) NOT NULL,
    [CategoryName]          NVARCHAR(15) NULL,
    [CategoryDescription]   NVARCHAR(MAX) NULL,
    [SupplierName]          NVARCHAR(40) NULL,
    [SupplierCountry]       NVARCHAR(15) NULL,
    [QuantityPerUnit]       NVARCHAR(20) NULL,
    [UnitPrice]             MONEY NULL,
    [Discontinued]          BIT NOT NULL,
    [ProductStatus]         NVARCHAR(15) NOT NULL,
    CONSTRAINT [PK_DimProduct] PRIMARY KEY CLUSTERED ([ProductKey] ASC)
);
GO

CREATE NONCLUSTERED INDEX [IX_DimProduct_ID] ON [dbo].[DimProduct] ([ProductID] ASC);
GO
