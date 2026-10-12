CREATE TABLE [dbo].[DimShipper](
    [ShipperKey]        INT IDENTITY(1,1) NOT NULL,
    [ShipperID]         INT NOT NULL,
    [CompanyName]       NVARCHAR(40) NOT NULL,
    [Phone]             NVARCHAR(24) NULL,
    CONSTRAINT [PK_DimShipper] PRIMARY KEY CLUSTERED ([ShipperKey] ASC)
);
GO