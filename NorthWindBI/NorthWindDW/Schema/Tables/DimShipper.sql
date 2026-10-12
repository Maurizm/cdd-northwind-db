CREATE TABLE [dbo].[DimShipper]
(
    [ShipperKey] [int] IDENTITY(1,1) NOT NULL,
    [ShipperCode] [int] NOT NULL,
    [CompanyName] [nvarchar](40) NOT NULL,
    [Phone] [nvarchar](24) NULL,
    CONSTRAINT [PK_DimShipper] PRIMARY KEY CLUSTERED ([ShipperKey] ASC)
);