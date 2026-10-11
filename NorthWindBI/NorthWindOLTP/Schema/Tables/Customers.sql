CREATE TABLE [dbo].[Customers]
(
    [CustomerID] [nchar](5) NOT NULL,
    [CompanyName] [nvarchar](40) NOT NULL,
    [ContactName] [nvarchar](30) NULL,
    [ContactTitle] [nvarchar](30) NULL,
    [Address] [nvarchar](60) NULL,
    [City] [nvarchar](15) NULL,
    [Region] [nvarchar](15) NULL,
    [PostalCode] [nvarchar](10) NULL,
    [Country] [nvarchar](15) NULL,
    [Phone] [nvarchar](24) NULL,
    [Fax] [nvarchar](24) NULL,
    [rowversion] [timestamp] NULL,
    CONSTRAINT [PK_Customers] PRIMARY KEY CLUSTERED ([CustomerID] ASC)
);
GO
CREATE NONCLUSTERED INDEX [City] ON [dbo].[Customers] ([City] ASC);
GO
CREATE NONCLUSTERED INDEX [CompanyName] ON [dbo].[Customers] ([CompanyName] ASC);
GO
CREATE NONCLUSTERED INDEX [PostalCode] ON [dbo].[Customers] ([PostalCode] ASC);
GO
CREATE NONCLUSTERED INDEX [Region] ON [dbo].[Customers] ([Region] ASC);