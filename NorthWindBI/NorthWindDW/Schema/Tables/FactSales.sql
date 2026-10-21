CREATE TABLE [dbo].[FactSales] (
    [SalesKey]          BIGINT IDENTITY(1,1) NOT NULL,
    [OrderDateKey]      INT NOT NULL,
    [ShippedDateKey]    INT NOT NULL,
    [RequiredDateKey]   INT NOT NULL,
    [CustomerKey]       INT NOT NULL,
    [EmployeeKey]       INT NOT NULL,
    [ProductKey]        INT NOT NULL,
    [SupplierKey]       INT NOT NULL,
    [ShipperKey]        INT NOT NULL,
    [OrderID]           INT NOT NULL,
    [OrderLineNum]      SMALLINT NOT NULL,
    [Quantity]          SMALLINT NOT NULL,
    [UnitPrice]         MONEY NOT NULL,
    [Discount]          REAL NOT NULL,
    [GrossAmount]       MONEY NOT NULL,
    [DiscountAmount]    MONEY NOT NULL,
    [NetAmount]         MONEY NOT NULL,
    [Freight]           MONEY NULL,
    [AllocatedFreight]  MONEY NULL,
    CONSTRAINT [PK_FactSales] PRIMARY KEY CLUSTERED ([SalesKey] ASC),
    CONSTRAINT [FK_FactSales_DimDate_Order]    FOREIGN KEY ([OrderDateKey])    REFERENCES [dbo].[DimDate]([DateKey]),
    CONSTRAINT [FK_FactSales_DimDate_Shipped]  FOREIGN KEY ([ShippedDateKey])  REFERENCES [dbo].[DimDate]([DateKey]),
    CONSTRAINT [FK_FactSales_DimDate_Required] FOREIGN KEY ([RequiredDateKey]) REFERENCES [dbo].[DimDate]([DateKey]),
    CONSTRAINT [FK_FactSales_DimCustomer]      FOREIGN KEY ([CustomerKey])     REFERENCES [dbo].[DimCustomer]([CustomerKey]),
    CONSTRAINT [FK_FactSales_DimEmployee]      FOREIGN KEY ([EmployeeKey])     REFERENCES [dbo].[DimEmployee]([EmployeeKey]),
    CONSTRAINT [FK_FactSales_DimProduct]       FOREIGN KEY ([ProductKey])      REFERENCES [dbo].[DimProduct]([ProductKey]),
    CONSTRAINT [FK_FactSales_DimSupplier]      FOREIGN KEY ([SupplierKey])     REFERENCES [dbo].[DimSupplier]([SupplierKey]),
    CONSTRAINT [FK_FactSales_DimShipper]       FOREIGN KEY ([ShipperKey])      REFERENCES [dbo].[DimShipper]([ShipperKey])
);
GO

CREATE NONCLUSTERED INDEX [IX_FactSales_OrderDateKey]    ON [dbo].[FactSales]([OrderDateKey] ASC);
GO
CREATE NONCLUSTERED INDEX [IX_FactSales_ShippedDateKey]  ON [dbo].[FactSales]([ShippedDateKey] ASC);
GO
CREATE NONCLUSTERED INDEX [IX_FactSales_CustomerKey]     ON [dbo].[FactSales]([CustomerKey] ASC);
GO
CREATE NONCLUSTERED INDEX [IX_FactSales_EmployeeKey]     ON [dbo].[FactSales]([EmployeeKey] ASC);
GO
CREATE NONCLUSTERED INDEX [IX_FactSales_ProductKey]      ON [dbo].[FactSales]([ProductKey] ASC);
GO
CREATE NONCLUSTERED INDEX [IX_FactSales_ShipperKey]      ON [dbo].[FactSales]([ShipperKey] ASC);
GO
CREATE NONCLUSTERED INDEX [IX_FactSales_SupplierKey]     ON [dbo].[FactSales]([SupplierKey] ASC);
GO
CREATE NONCLUSTERED INDEX [IX_FactSales_OrderID]         ON [dbo].[FactSales]([OrderID] ASC);
GO
