USE NorthWindDW;
GO
IF OBJECT_ID('dbo.FactSales','U') IS NULL
BEGIN
    CREATE TABLE dbo.FactSales
    (
        SalesKey          bigint IDENTITY(1,1) NOT NULL CONSTRAINT PK_FactSales PRIMARY KEY,
        OrderID           int NOT NULL, -- dimensión degenerada: identificador del pedido de origen
        OrderLineNumber   int NOT NULL, -- ProductID identifica el producto dentro del pedido en NorthWind
        OrderDateKey      int NOT NULL,
        RequiredDateKey   int NOT NULL,
        ShippedDateKey    int NOT NULL,
        CustomerKey       int NOT NULL,
        ProductKey        int NOT NULL,
        EmployeeKey       int NOT NULL,
        ShipperKey        int NOT NULL,
        ShipToKey         int NOT NULL,
        Quantity          smallint NOT NULL,
        UnitPrice         decimal(19,4) NOT NULL,
        DiscountRate      decimal(9,6) NOT NULL,
        GrossAmount       decimal(19,4) NOT NULL,
        DiscountAmount    decimal(19,4) NOT NULL,
        NetAmount         decimal(19,4) NOT NULL,
        FreightOrderAmount decimal(19,4) NULL, -- importe original del flete del pedido; no sumar por línea
        CONSTRAINT UQ_FactSales_OrderLine UNIQUE (OrderID, OrderLineNumber),
        CONSTRAINT FK_FactSales_OrderDate FOREIGN KEY (OrderDateKey) REFERENCES dbo.DimDate(DateKey),
        CONSTRAINT FK_FactSales_RequiredDate FOREIGN KEY (RequiredDateKey) REFERENCES dbo.DimDate(DateKey),
        CONSTRAINT FK_FactSales_ShippedDate FOREIGN KEY (ShippedDateKey) REFERENCES dbo.DimDate(DateKey),
        CONSTRAINT FK_FactSales_Customer FOREIGN KEY (CustomerKey) REFERENCES dbo.DimCustomer(CustomerKey),
        CONSTRAINT FK_FactSales_Product FOREIGN KEY (ProductKey) REFERENCES dbo.DimProduct(ProductKey),
        CONSTRAINT FK_FactSales_Employee FOREIGN KEY (EmployeeKey) REFERENCES dbo.DimEmployee(EmployeeKey),
        CONSTRAINT FK_FactSales_Shipper FOREIGN KEY (ShipperKey) REFERENCES dbo.DimShipper(ShipperKey),
        CONSTRAINT FK_FactSales_ShipTo FOREIGN KEY (ShipToKey) REFERENCES dbo.DimShipTo(ShipToKey),
        CONSTRAINT CK_FactSales_Discount CHECK (DiscountRate >= 0 AND DiscountRate <= 1)
    );
    CREATE INDEX IX_FactSales_OrderDate ON dbo.FactSales(OrderDateKey);
    CREATE INDEX IX_FactSales_Customer ON dbo.FactSales(CustomerKey);
    CREATE INDEX IX_FactSales_Product ON dbo.FactSales(ProductKey);
END;
GO
