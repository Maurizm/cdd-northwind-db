CREATE TABLE [dbo].[FactSales](
    [SalesKey]          BIGINT IDENTITY(1,1) NOT NULL,
    [OrderID]           INT NOT NULL,
    [LineNumber]        TINYINT NOT NULL,
    [ProductKey]        INT NOT NULL,
    [CustomerKey]       INT NOT NULL,
    [EmployeeKey]       INT NOT NULL,
    [ShipperKey]        INT NOT NULL,
    [OrderDateKey]      INT NOT NULL,
    [ShipDateKey]       INT NULL,
    [RequiredDateKey]   INT NULL,
    [UnitPrice]         MONEY NOT NULL,
    [Quantity]          SMALLINT NOT NULL,
    [Discount]          REAL NOT NULL,
    [ExtendedPrice]     MONEY NOT NULL,
    [Freight]           MONEY NULL,
    [GrossProfit]       MONEY NOT NULL,
    CONSTRAINT [PK_FactSales] PRIMARY KEY CLUSTERED ([SalesKey] ASC)
);
GO  
ALTER TABLE [dbo].[FactSales] ADD CONSTRAINT [FK_FactSales_DimProduct]
    FOREIGN KEY ([ProductKey]) REFERENCES [dbo].[DimProduct] ([ProductKey]);
GO

ALTER TABLE [dbo].[FactSales] ADD CONSTRAINT [FK_FactSales_DimCustomer]
    FOREIGN KEY ([CustomerKey]) REFERENCES [dbo].[DimCustomer] ([CustomerKey]);
GO

ALTER TABLE [dbo].[FactSales] ADD CONSTRAINT [FK_FactSales_DimEmployee]
    FOREIGN KEY ([EmployeeKey]) REFERENCES [dbo].[DimEmployee] ([EmployeeKey]);
GO

ALTER TABLE [dbo].[FactSales] ADD CONSTRAINT [FK_FactSales_DimShipper]
    FOREIGN KEY ([ShipperKey]) REFERENCES [dbo].[DimShipper] ([ShipperKey]);
GO

ALTER TABLE [dbo].[FactSales] ADD CONSTRAINT [FK_FactSales_DimDate_Order]
    FOREIGN KEY ([OrderDateKey]) REFERENCES [dbo].[DimDate] ([DateKey]);
GO

ALTER TABLE [dbo].[FactSales] ADD CONSTRAINT [FK_FactSales_DimDate_Ship]
    FOREIGN KEY ([ShipDateKey]) REFERENCES [dbo].[DimDate] ([DateKey]);
GO

ALTER TABLE [dbo].[FactSales] ADD CONSTRAINT [FK_FactSales_DimDate_Required]
    FOREIGN KEY ([RequiredDateKey]) REFERENCES [dbo].[DimDate] ([DateKey]);
GO
CREATE NONCLUSTERED INDEX [IX_FactSales_ProductKey] 
    ON [dbo].[FactSales] ([ProductKey]);
GO

CREATE NONCLUSTERED INDEX [IX_FactSales_CustomerKey] 
    ON [dbo].[FactSales] ([CustomerKey]);
GO

CREATE NONCLUSTERED INDEX [IX_FactSales_EmployeeKey] 
    ON [dbo].[FactSales] ([EmployeeKey]);
GO

CREATE NONCLUSTERED INDEX [IX_FactSales_OrderDateKey] 
    ON [dbo].[FactSales] ([OrderDateKey]);
GO

CREATE NONCLUSTERED INDEX [IX_FactSales_OrderID] 
    ON [dbo].[FactSales] ([OrderID]);
GO

CREATE UNIQUE NONCLUSTERED INDEX [IX_DimCustomer_CustomerID] 
    ON [dbo].[DimCustomer] ([CustomerID]) WHERE [IsCurrent] = 1;
GO


CREATE UNIQUE NONCLUSTERED INDEX [IX_DimProduct_ProductID] 
    ON [dbo].[DimProduct] ([ProductID]) WHERE [IsCurrent] = 1;
GO

CREATE UNIQUE NONCLUSTERED INDEX [IX_DimShipper_ShipperID] 
    ON [dbo].[DimShipper] ([ShipperID]);
GO