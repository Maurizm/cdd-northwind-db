CREATE TABLE [dbo].[DimProduct]
(
    [ProductKey] [int] IDENTITY(1,1) NOT NULL,
    [ProductCode] [int] NOT NULL,
    [ProductName] [nvarchar](40) NOT NULL,
    [CategoryName] [nvarchar](15) NULL,
    [SupplierName] [nvarchar](40) NULL,
    [SupplierCountry] [nvarchar](15) NULL,
    [QuantityPerUnit] [nvarchar](20) NULL,
    [ListUnitPrice] [money] NULL,
    [Discontinued] [bit] NOT NULL,
    [ProductStatus] [nvarchar](15) NOT NULL,
    CONSTRAINT [PK_DimProduct] PRIMARY KEY CLUSTERED ([ProductKey] ASC)
);
GO
CREATE UNIQUE NONCLUSTERED INDEX [IX_DimProduct_Code] ON [dbo].[DimProduct] ([ProductCode] ASC);