CREATE TABLE [dbo].[DimCustomer]
(
    [CustomerKey] [int] IDENTITY(1,1) NOT NULL,
    [CustomerCode] [nvarchar](5) NOT NULL,
    [CompanyName] [nvarchar](40) NOT NULL,
    [ContactName] [nvarchar](30) NULL,
    [ContactTitle] [nvarchar](30) NULL,
    [City] [nvarchar](15) NULL,
    [Region] [nvarchar](15) NULL,
    [PostalCode] [nvarchar](10) NULL,
    [Country] [nvarchar](15) NULL,
    [Phone] [nvarchar](24) NULL,
    CONSTRAINT [PK_DimCustomer] PRIMARY KEY CLUSTERED ([CustomerKey] ASC)
);
GO
CREATE UNIQUE NONCLUSTERED INDEX [IX_DimCustomer_Code] ON [dbo].[DimCustomer] ([CustomerCode] ASC);