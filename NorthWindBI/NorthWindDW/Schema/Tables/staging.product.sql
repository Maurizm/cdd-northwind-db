CREATE TABLE [staging].[product]
(
    [ProductID]           INT           NOT NULL,
    [ProductName]         NVARCHAR(40)  NOT NULL,
    [SupplierID]          INT           NULL,
    [CategoryName]        NVARCHAR(15)  NULL,
    [CategoryDescription] NVARCHAR(MAX) NULL,
    [QuantityPerUnit]     NVARCHAR(20)  NULL,
    [ListUnitPrice]       MONEY         NULL,
    [Discontinued]        BIT           NOT NULL,
    [ProductStatus]       NVARCHAR(15)  NOT NULL
);
GO
