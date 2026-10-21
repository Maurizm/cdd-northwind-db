CREATE TABLE [dbo].[DimSupplier] (
    [SupplierKey]   INT IDENTITY(1,1) NOT NULL,
    [SupplierID]    INT NOT NULL,
    [CompanyName]   NVARCHAR(40) NOT NULL,
    [ContactName]   NVARCHAR(30) NULL,
    [ContactTitle]  NVARCHAR(30) NULL,
    [Address]       NVARCHAR(60) NULL,
    [PostalCode]    NVARCHAR(10) NULL,
    [Phone]         NVARCHAR(24) NULL,
    [Fax]           NVARCHAR(24) NULL,
    [HomePage]      NVARCHAR(MAX) NULL,
    [GeographyKey]  INT NOT NULL,
    CONSTRAINT [PK_DimSupplier] PRIMARY KEY CLUSTERED ([SupplierKey] ASC),
    CONSTRAINT [FK_DimSupplier_DimGeography] FOREIGN KEY ([GeographyKey]) REFERENCES [dbo].[DimGeography]([GeographyKey])
);
GO

CREATE NONCLUSTERED INDEX [IX_DimSupplier_ID] ON [dbo].[DimSupplier] ([SupplierID] ASC);
GO
