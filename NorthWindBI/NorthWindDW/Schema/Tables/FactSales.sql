CREATE TABLE [dbo].[FactSales]
(
    [SalesKey] [bigint] IDENTITY(1,1) NOT NULL,
    [OrderDateKey] [int] NOT NULL,
    [ShippedDateKey] [int] NOT NULL,
    [CustomerKey] [int] NOT NULL,
    [EmployeeKey] [int] NOT NULL,
    [ProductKey] [int] NOT NULL,
    [ShipperKey] [int] NOT NULL,
    [OrderID] [int] NOT NULL,
    [OrderLineNum] [smallint] NOT NULL,
    [OrderQty] [smallint] NOT NULL,
    [UnitPrice] [money] NOT NULL,
    [DiscountRate] [real] NOT NULL,
    [GrossAmount] [money] NOT NULL,
    [DiscountAmount] [money] NOT NULL,
    [NetAmount] [money] NOT NULL,
    CONSTRAINT [PK_FactSales] PRIMARY KEY CLUSTERED ([SalesKey] ASC)
);
GO
ALTER TABLE [dbo].[FactSales] ADD CONSTRAINT [FK_Fact_DimDate]     FOREIGN KEY ([OrderDateKey])   REFERENCES [dbo].[DimDate] ([DateKey]);
GO
ALTER TABLE [dbo].[FactSales] ADD CONSTRAINT [FK_Fact_DimShipped]  FOREIGN KEY ([ShippedDateKey]) REFERENCES [dbo].[DimDate] ([DateKey]);
GO
ALTER TABLE [dbo].[FactSales] ADD CONSTRAINT [FK_Fact_DimCustomer] FOREIGN KEY ([CustomerKey])    REFERENCES [dbo].[DimCustomer] ([CustomerKey]);
GO
ALTER TABLE [dbo].[FactSales] ADD CONSTRAINT [FK_Fact_DimEmployee] FOREIGN KEY ([EmployeeKey])    REFERENCES [dbo].[DimEmployee] ([EmployeeKey]);
GO
ALTER TABLE [dbo].[FactSales] ADD CONSTRAINT [FK_Fact_DimProduct]  FOREIGN KEY ([ProductKey])     REFERENCES [dbo].[DimProduct] ([ProductKey]);
GO
ALTER TABLE [dbo].[FactSales] ADD CONSTRAINT [FK_Fact_DimShipper]  FOREIGN KEY ([ShipperKey])     REFERENCES [dbo].[DimShipper] ([ShipperKey]);
GO
CREATE NONCLUSTERED INDEX [IX_Fact_OrderDateKey] ON [dbo].[FactSales] ([OrderDateKey] ASC);
GO
CREATE NONCLUSTERED INDEX [IX_Fact_ShippedDateKey] ON [dbo].[FactSales] ([ShippedDateKey] ASC);
GO
CREATE NONCLUSTERED INDEX [IX_Fact_CustomerKey] ON [dbo].[FactSales] ([CustomerKey] ASC);
GO
CREATE NONCLUSTERED INDEX [IX_Fact_EmployeeKey] ON [dbo].[FactSales] ([EmployeeKey] ASC);
GO
CREATE NONCLUSTERED INDEX [IX_Fact_ProductKey] ON [dbo].[FactSales] ([ProductKey] ASC);
GO
CREATE NONCLUSTERED INDEX [IX_Fact_ShipperKey] ON [dbo].[FactSales] ([ShipperKey] ASC);
GO
CREATE NONCLUSTERED INDEX [IX_Fact_OrderID] ON [dbo].[FactSales] ([OrderID] ASC);